import io
import base64
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from django.db import models


class Statistic:
    def __init__(self, vacancies):
        self.vacancies = vacancies
        self.vacancies_with_salary = vacancies.exclude(salary__isnull=True)
        self.insights = []

    def fig_to_base64(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)
        return img_base64

    def add_insight(self, category, title, description, value=None, unit=''):
        insight = {
            'category': category,
            'title': title,
            'description': description,
            'value': value,
            'unit': unit
        }
        self.insights.append(insight)
        return insight

    def get_base_statistics(self):

        salary_stats = self.vacancies.exclude(salary__isnull=True).aggregate(
            avg=models.Avg('salary'),
            min=models.Min('salary'),
            max=models.Max('salary'),
            count=models.Count('salary')
        )

        salary_distribution_data = self.salary_distribution_chart()
        experience_data = self.salary_by_experience_chart()
        platform_data = self.platform_comparison_chart()
        education_data = self.education_chart()

        metrics = {
            'total': self.vacancies.count(),
            'with_salary': self.vacancies_with_salary.count(),
            'avg_salary': int(salary_stats['avg'] or 0),
            'min_salary': salary_stats['min'] or 0,
            'max_salary': salary_stats['max'] or 0,
            'salary_distribution': salary_distribution_data['image'] if salary_distribution_data else None,
            'salary_distribution_insights': salary_distribution_data['insights'] if salary_distribution_data else [],
            'experience_chart': experience_data['image'] if experience_data else None,
            'experience_insights': experience_data['insights'] if experience_data else [],
            'platform_comparison': platform_data['image'] if platform_data else None,
            'platform_insights': platform_data['insights'] if platform_data else [],
            'education_charts': education_data['image'] if education_data else None,
            'education_insights': education_data['insights'] if education_data else [],
            'all_insights': self.insights,
        }

        self.generate_overall_insights(metrics)

        return metrics

    def generate_overall_insights(self, metrics):
        if metrics['with_salary'] > 0:

            salary_range = metrics['max_salary'] - metrics['min_salary']
            salary_dispersion = salary_range / metrics['avg_salary'] * 100 if metrics['avg_salary'] > 0 else 0

            self.add_insight(
                category='overall',
                title='Диапазон зарплат',
                description=f'Зарплаты варьируются от {metrics["min_salary"]:,} до {metrics["max_salary"]:,} руб.',
                value=f'{salary_dispersion:.1f}%',
                unit='дисперсия'
            )


            salary_coverage = (metrics['with_salary'] / metrics['total']) * 100
            self.add_insight(
                category='overall',
                title='Полнота данных',
                description=f'Зарплата указана в {salary_coverage:.1f}% вакансий',
                value=f'{metrics["with_salary"]}/{metrics["total"]}',
                unit='вакансий'
            )

    def salary_distribution_chart(self):
        if not self.vacancies_with_salary.exists():
            return None

        salaries = list(self.vacancies_with_salary.values_list('salary', flat=True))

        if len(salaries) < 3:
            return None

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        insights = []

        mean_salary = np.mean(salaries)
        median_salary = np.median(salaries)
        std_salary = np.std(salaries)
        q25 = np.percentile(salaries, 25)
        q75 = np.percentile(salaries, 75)

        n, bins, patches = axes[0].hist(salaries, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0].axvline(mean_salary, color='red', linestyle='--',
                        label=f'Среднее: {int(mean_salary):,} руб.')
        axes[0].axvline(median_salary, color='green', linestyle='--',
                        label=f'Медиана: {int(median_salary):,} руб.')
        axes[0].set_xlabel('Зарплата (руб.)')
        axes[0].set_ylabel('Количество вакансий')
        axes[0].set_title('Распределение зарплат')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        axes[1].boxplot(salaries, vert=False, patch_artist=True,
                        boxprops=dict(facecolor='lightblue'),
                        medianprops=dict(color='red'))
        axes[1].set_xlabel('Зарплата (руб.)')
        axes[1].set_title('Разброс зарплат')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()


        mean_median_diff = abs(mean_salary - median_salary)
        mean_median_ratio = mean_median_diff / mean_salary * 100

        if mean_median_ratio > 20:
            insight_text = "Значительная разница между средней и медианной зарплатой указывает на наличие высокооплачиваемых выбросов."
        else:
            insight_text = "Средняя и медианная зарплаты близки, что говорит о равномерном распределении."

        insights.append({
            'title': 'Средняя vs Медиана',
            'description': insight_text,
            'details': f'Средняя: {int(mean_salary):,} руб., Медиана: {int(median_salary):,} руб.',
            'recommendation': 'Ориентируйтесь на медиану как на более устойчивый показатель.'
        })

        salary_range = max(salaries) - min(salaries)
        coef_variation = (std_salary / mean_salary) * 100 if mean_salary > 0 else 0

        if coef_variation > 50:
            range_text = "Высокий разброс зарплат. Рынок нестабилен или представлены позиции разного уровня."
        elif coef_variation > 30:
            range_text = "Умеренный разброс зарплат. Стандартная ситуация для рынка."
        else:
            range_text = "Низкий разброс зарплат. Зарплаты на рынке довольно предсказуемы."

        insights.append({
            'title': 'Разброс зарплат',
            'description': range_text,
            'details': f'Разброс: {int(salary_range):,} руб. (от {min(salaries):,} до {max(salaries):,} руб.)',
            'recommendation': 'Изучите требования к позициям с высокой зарплатой.'
        })


        insights.append({
            'title': 'Середина рынка',
            'description': f'50% вакансий предлагают зарплату от {int(q25):,} до {int(q75):,} руб.',
            'details': f'25-й перцентиль: {int(q25):,} руб., 75-й перцентиль: {int(q75):,} руб.',
            'recommendation': 'Это диапазон, в котором стоит искать стандартные предложения.'
        })

        return {
            'image': self.fig_to_base64(fig),
            'insights': insights,
            'stats': {
                'mean': int(mean_salary),
                'median': int(median_salary),
                'std': int(std_salary),
                'q25': int(q25),
                'q75': int(q75),
                'min': int(min(salaries)),
                'max': int(max(salaries))
            }
        }

    def salary_by_experience_chart(self):
        if not self.vacancies_with_salary.exists():
            return None

        # Группируем зарплаты по опыту
        experience_data = {}
        experience_labels = {
            'not_experience': 'Без опыта',
            '1year': 'От 1 года',
            '3year': 'От 3 лет',
            '6year': 'От 6 лет',
            '10year': 'От 10 лет',
        }

        insights = []

        for exp_key, exp_label in experience_labels.items():
            salaries = list(self.vacancies_with_salary.filter(
                experience=exp_label
            ).values_list('salary', flat=True))
            if salaries and len(salaries) > 1:
                experience_data[exp_label] = salaries

        if not experience_data:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        labels = list(experience_data.keys())
        data = list(experience_data.values())


        bp = ax.boxplot(data, labels=labels, patch_artist=True,
                        medianprops=dict(color='red'),
                        boxprops=dict(facecolor='lightblue'))


        means = [np.mean(d) for d in data]
        ax.scatter(range(1, len(labels) + 1), means, color='green',
                   s=100, zorder=3, label='Среднее')

        ax.set_ylabel('Зарплата (руб.)')
        ax.set_title('Зарплата в зависимости от требуемого опыта')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if len(data) >= 2:
            exp_levels = list(range(len(labels)))
            median_salaries = [np.median(d) for d in data]

            for i in range(1, len(median_salaries)):
                if median_salaries[i - 1] > 0:
                    growth = ((median_salaries[i] - median_salaries[i - 1]) / median_salaries[i - 1]) * 100

                    if growth > 0:
                        insights.append({
                            'title': f'Рост от {labels[i - 1]} к {labels[i]}',
                            'description': f'Зарплата увеличивается на {growth:.1f}%',
                            'details': f'{int(median_salaries[i - 1]):,} → {int(median_salaries[i]):,} руб.',
                            'recommendation': 'Опыт окупается в виде более высокой зарплаты.'
                        })

            max_median_idx = np.argmax(median_salaries)
            min_median_idx = np.argmin(median_salaries)

            insights.append({
                'title': 'Наиболее оплачиваемый опыт',
                'description': f'{labels[max_median_idx]} - самый высокооплачиваемый уровень',
                'details': f'Медианная зарплата: {int(median_salaries[max_median_idx]):,} руб.',
                'recommendation': f'Стремитесь к уровню {labels[max_median_idx]} для максимального дохода'
            })

            total_growth = ((median_salaries[-1] - median_salaries[0]) / median_salaries[0] * 100) if median_salaries[
                                                                                                          0] > 0 else 0
            insights.append({
                'title': 'Общий рост зарплаты',
                'description': f'За весь карьерный путь зарплата может вырасти на {total_growth:.1f}%',
                'details': f'От {int(median_salaries[0]):,} до {int(median_salaries[-1]):,} руб.',
                'recommendation': 'Инвестируйте в опыт и профессиональное развитие'
            })

        return {
            'image': self.fig_to_base64(fig),
            'insights': insights,
            'stats': {
                'labels': labels,
                'medians': [int(np.median(d)) for d in data],
                'means': [int(np.mean(d)) for d in data],
                'counts': [len(d) for d in data]
            }
        }

    def platform_comparison_chart(self):
        if not self.vacancies.exists():
            return None

        platform_stats = self.vacancies.values('aggregator').annotate(
            count=models.Count('id'),
            avg_salary=models.Avg('salary'),
        ).order_by('-count')

        if not platform_stats:
            return None

        insights = []

        platforms = [p['aggregator'] for p in platform_stats]
        counts = [p['count'] for p in platform_stats]
        avg_salaries = [p['avg_salary'] or 0 for p in platform_stats]

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        colors = plt.cm.Set3(np.linspace(0, 1, len(platforms)))
        axes[0].pie(counts, labels=platforms, autopct='%1.1f%%',
                    colors=colors, startangle=90)
        axes[0].set_title('Распределение вакансий по платформам')

        x = np.arange(len(platforms))
        width = 0.35

        axes[1].bar(x, avg_salaries, width, color='skyblue', alpha=0.8)
        axes[1].set_xlabel('Платформы')
        axes[1].set_ylabel('Средняя зарплата (руб.)')
        axes[1].set_title('Средняя зарплата по платформам')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(platforms, rotation=45)
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        if len(platforms) >= 2:
            max_count_idx = np.argmax(counts)
            insights.append({
                'title': 'Самая популярная платформа',
                'description': f'{platforms[max_count_idx]} лидирует по количеству вакансий',
                'details': f'{counts[max_count_idx]} вакансий ({counts[max_count_idx] / sum(counts) * 100:.1f}%)',
                'recommendation': 'Начинайте поиск с этой платформы'
            })

            max_salary_idx = np.argmax(avg_salaries)
            insights.append({
                'title': 'Платформа с самыми высокими зарплатами',
                'description': f'{platforms[max_salary_idx]} предлагает самые высокие зарплаты',
                'details': f'Средняя зарплата: {int(avg_salaries[max_salary_idx]):,} руб.',
                'recommendation': 'Ищите высокооплачиваемые вакансии здесь'
            })

            # Разница между платформами
            if avg_salaries[max_salary_idx] > 0 and avg_salaries[
                min(range(len(avg_salaries)), key=avg_salaries.__getitem__)] > 0:
                salary_ratio = avg_salaries[max_salary_idx] / avg_salaries[
                    min(range(len(avg_salaries)), key=avg_salaries.__getitem__)]
                insights.append({
                    'title': 'Разница между платформами',
                    'description': f'Зарплаты различаются в {salary_ratio:.1f} раза между платформами',
                    'details': 'Некоторые платформы специализируются на разных уровнях позиций',
                    'recommendation': 'Используйте несколько платформ для полного охвата рынка'
                })

        return {
            'image': self.fig_to_base64(fig),
            'insights': insights,
            'stats': {
                'platforms': platforms,
                'counts': counts,
                'avg_salaries': [int(s) for s in avg_salaries],
                'total_vacancies': sum(counts)
            }
        }

    def education_chart(self):
        if not self.vacancies.exists():
            return None

        education_stats = self.vacancies.values('education').annotate(
            count=models.Count('id'),
            avg_salary=models.Avg('salary')
        ).order_by('-count')

        if not education_stats:
            return None

        education_labels = {
            'not_important': 'Не важно',
            'secondary': 'Среднее',
            'higher': 'Высшее',
            'half_higher': 'Неполное высшее',
            'any': 'Любое',
        }

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [education_labels.get(e['education'], e['education'])
                  for e in education_stats]
        counts = [e['count'] for e in education_stats]
        avg_salaries = [e['avg_salary'] or 0 for e in education_stats]

        ax1 = ax
        ax2 = ax1.twinx()

        bars = ax1.bar(labels, counts, color='lightblue', alpha=0.7,
                       label='Количество вакансий')
        ax1.set_xlabel('Требуемое образование')
        ax1.set_ylabel('Количество вакансий', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')


        line = ax2.plot(labels, avg_salaries, color='red', marker='o',
                        linewidth=2, markersize=8, label='Средняя зарплата')
        ax2.set_ylabel('Средняя зарплата (руб.)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                     f'{count}', ha='center', va='bottom')

        lines_labels = [ax1.get_legend_handles_labels(), ax2.get_legend_handles_labels()]
        lines, labels_legend = [sum(lol, []) for lol in zip(*lines_labels)]
        ax1.legend(lines, labels_legend, loc='upper left')

        ax1.set_title('Требования к образованию')
        plt.xticks(rotation=45)
        plt.tight_layout()

        insights = []

        if len(labels) >= 2:
            max_count_idx = np.argmax(counts)
            insights.append({
                'title': 'Самые частые требования',
                'description': f'Чаще всего требуется: {labels[max_count_idx]}',
                'details': f'{counts[max_count_idx]} вакансий ({counts[max_count_idx] / sum(counts) * 100:.1f}%)',
                'recommendation': 'Соответствуйте этим требованиям для большего выбора'
            })


            valid_salaries = [(i, s) for i, s in enumerate(avg_salaries) if s > 0]
            if valid_salaries:
                max_salary_idx = max(valid_salaries, key=lambda x: x[1])[0]
                insights.append({
                    'title': 'Образование и зарплата',
                    'description': f'Высшее образование даёт самую высокую зарплату',
                    'details': f'Средняя зарплата: {int(avg_salaries[max_salary_idx]):,} руб.',
                    'recommendation': 'Рассмотрите получение высшего образования для повышения дохода'
                })


            if 'Высшее' in labels and 'Не важно' in labels:
                idx_higher = labels.index('Высшее')
                idx_not_important = labels.index('Не важно')
                if avg_salaries[idx_higher] > 0 and avg_salaries[idx_not_important] > 0:
                    salary_difference = avg_salaries[idx_higher] - avg_salaries[idx_not_important]
                    salary_ratio = avg_salaries[idx_higher] / avg_salaries[idx_not_important]

                    insights.append({
                        'title': 'Преимущество образования',
                        'description': f'Высшее образование даёт зарплату в {salary_ratio:.1f} раза выше',
                        'details': f'Разница: {int(salary_difference):,} руб. в месяц',
                        'recommendation': 'Образование значительно влияет на уровень дохода'
                    })

        return {
            'image': self.fig_to_base64(fig),
            'insights': insights,
            'stats': {
                'labels': labels,
                'counts': counts,
                'avg_salaries': [int(s) for s in avg_salaries],
                'total': sum(counts)
            }
        }

