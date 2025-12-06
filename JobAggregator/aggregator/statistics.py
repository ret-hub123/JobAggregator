import io
import base64


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy
from django.db import models



class Statistic:
    def __init__(self, vacancies):
        self.vacancies = vacancies
        self.vacancies_with_salary = vacancies.exclude(salary__isnull=True)

    def fig_to_base64(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)
        return img_base64

    def get_base_statistics(self):

        salary_stats = self.vacancies.exclude(salary__isnull=True).aggregate(
            avg=models.Avg('salary'),
            min=models.Min('salary'),
            max=models.Max('salary'))

        metrics  = {
            'total': self.vacancies.count(),
            'with_salary': self.vacancies.exclude(salary__isnull=True).count(),
            'avg_salary': int(salary_stats['avg']),
            'min_salary': salary_stats['min'],
            'max_salary': salary_stats['max'],
            'salary_distribution': self.salary_distribution_chart,
            'experience_chart': self.salary_by_experience_chart,
            'platform_comparison': self.platform_comparison_chart,
            'education_charts': self.education_chart,
        }

        return metrics

    def salary_distribution_chart(self):

        if not self.vacancies_with_salary.exists():
            return None

        salaries = list(self.vacancies_with_salary.values_list('salary', flat=True))

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Гистограмма
        axes[0].hist(salaries, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0].axvline(numpy.mean(salaries), color='red', linestyle='--', label=f'Среднее: {int(numpy.mean(salaries)):}')
        axes[0].axvline(numpy.median(salaries), color='green', linestyle='--',
                        label=f'Медиана: {int(numpy.median(salaries)):,}')
        axes[0].set_xlabel('Зарплата (руб.)')
        axes[0].set_ylabel('Количество вакансий')
        axes[0].set_title('Распределение зарплат')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Box plot
        axes[1].boxplot(salaries, vert=False, patch_artist=True,
                        boxprops=dict(facecolor='lightblue'),
                        medianprops=dict(color='red'))
        axes[1].set_xlabel('Зарплата (руб.)')
        axes[1].set_title('Разброс зарплат')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        return self.fig_to_base64(fig)



    def salary_distribution_chart(self):

            if not self.vacancies_with_salary.exists():
                return None

            salaries = list(self.vacancies_with_salary.values_list('salary', flat=True))

            # Если зарплат слишком мало, не строим график
            if len(salaries) < 3:
                return None

            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            # Гистограмма
            axes[0].hist(salaries, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
            axes[0].axvline(numpy.mean(salaries), color='red', linestyle='--',
                            label=f'Среднее: {int(numpy.mean(salaries)):,}')
            axes[0].axvline(numpy.median(salaries), color='green', linestyle='--',
                            label=f'Медиана: {int(numpy.median(salaries)):,}')
            axes[0].set_xlabel('Зарплата (руб.)')
            axes[0].set_ylabel('Количество вакансий')
            axes[0].set_title('Распределение зарплат')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # Box plot
            axes[1].boxplot(salaries, vert=False, patch_artist=True,
                            boxprops=dict(facecolor='lightblue'),
                            medianprops=dict(color='red'))
            axes[1].set_xlabel('Зарплата (руб.)')
            axes[1].set_title('Разброс зарплат')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            return self.fig_to_base64(fig)

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

            for exp_key, exp_label in experience_labels.items():
                salaries = list(self.vacancies_with_salary.filter(
                    experience=exp_label
                ).values_list('salary', flat=True))
                if salaries and len(salaries) > 1:  # Нужно хотя бы 2 точки для box plot
                    experience_data[exp_label] = salaries

            if not experience_data:
                return None

            fig, ax = plt.subplots(figsize=(10, 6))

            labels = list(experience_data.keys())
            data = list(experience_data.values())


            bp = ax.boxplot(data, labels=labels, patch_artist=True,
                            medianprops=dict(color='red', linewidth=2),
                            boxprops=dict(facecolor='lightblue', alpha=0.7))


            means = [numpy.mean(d) for d in data]
            ax.scatter(range(1, len(labels) + 1), means, color='green',
                       s=100, zorder=3, label='Среднее')

            ax.set_ylabel('Зарплата (руб.)')
            ax.set_title('Зарплата в зависимости от требуемого опыта')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()

            return self.fig_to_base64(fig)

    def platform_comparison_chart(self):
        """Сравнение платформ"""
        if not self.vacancies.exists():
            return None

        # Статистика по платформам - сначала получаем количество вакансий
        platform_counts = self.vacancies.values('aggregator').annotate(
            count=models.Count('id')
        ).order_by('-count')

        # Вычисляем среднюю зарплату отдельно
        platform_avg_salary = self.vacancies.exclude(salary__isnull=True).values('aggregator').annotate(
            avg_salary=models.Avg('salary')
        )

        # Создаем словарь для хранения данных
        platform_data = {}

        for p in platform_counts:
            platform_data[p['aggregator']] = {
                'count': p['count'],
                'avg_salary': 0,
                'median_salary': 0
            }

        # Заполняем средние зарплаты
        for p in platform_avg_salary:
            if p['aggregator'] in platform_data:
                platform_data[p['aggregator']]['avg_salary'] = p['avg_salary']

        # Вычисляем медианные зарплаты для каждой платформы
        for platform in platform_data.keys():
            salaries = list(self.vacancies.filter(
                aggregator=platform
            ).exclude(salary__isnull=True).values_list('salary', flat=True))

            if salaries:
                # Вычисляем медиану в Python
                sorted_salaries = sorted(salaries)
                n = len(sorted_salaries)
                if n % 2 == 1:
                    median_salary = sorted_salaries[n // 2]
                else:
                    median_salary = (sorted_salaries[n // 2 - 1] + sorted_salaries[n // 2]) / 2
                platform_data[platform]['median_salary'] = median_salary
            else:
                platform_data[platform]['median_salary'] = 0

        if not platform_data:
            return None

        # Подготавливаем данные для графика
        platforms = list(platform_data.keys())
        counts = [platform_data[p]['count'] for p in platforms]
        avg_salaries = [platform_data[p]['avg_salary'] for p in platforms]
        median_salaries = [platform_data[p]['median_salary'] for p in platforms]

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Круговая диаграмма количества вакансий
        colors = plt.cm.Set3(numpy.linspace(0, 1, len(platforms)))
        axes[0].pie(counts, labels=platforms, autopct='%1.1f%%',
                    colors=colors, startangle=90)
        axes[0].set_title('Распределение вакансий по платформам')

        # Столбчатая диаграмма зарплат
        x = numpy.arange(len(platforms))
        width = 0.35

        axes[1].bar(x - width / 2, avg_salaries, width, label='Средняя',
                    color='skyblue', alpha=0.8)
        axes[1].bar(x + width / 2, median_salaries, width, label='Медиана',
                    color='lightgreen', alpha=0.8)
        axes[1].set_xlabel('Платформы')
        axes[1].set_ylabel('Зарплата (руб.)')
        axes[1].set_title('Сравнение зарплат по платформам')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(platforms, rotation=45)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        return self.fig_to_base64(fig)

    def education_chart(self):
        """Требования к образованию"""
        if not self.vacancies.exists():
            return None

        # Статистика по образованию
        education_stats = self.vacancies.values('education').annotate(
            count=models.Count('id'),
            avg_salary=models.Avg('salary')
        ).order_by('-count')

        if not education_stats:
            return None

        # Словарь для перевода ключей в читаемый вид
        education_labels = {
            'not_important': 'Не имеет значения',
            'secondary': 'Среднее профессиональное',
            'higher': 'Высшее',
            'half_higher': 'Неполное высшее',
            'any': 'Любое',
        }

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [education_labels.get(e['education'], e['education'])
                  for e in education_stats]
        counts = [e['count'] for e in education_stats]
        avg_salaries = [e['avg_salary'] or 0 for e in education_stats]

        # Создаем два Y-оси
        ax1 = ax
        ax2 = ax1.twinx()

        # Гистограмма количества
        bars = ax1.bar(labels, counts, color='lightblue', alpha=0.7,
                       label='Количество вакансий')
        ax1.set_xlabel('Требуемое образование')
        ax1.set_ylabel('Количество вакансий', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Линия средних зарплат
        line = ax2.plot(labels, avg_salaries, color='red', marker='o',
                        linewidth=2, markersize=8, label='Средняя зарплата')
        ax2.set_ylabel('Средняя зарплата (руб.)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        # Добавляем значения на столбцы
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                     f'{count}', ha='center', va='bottom')

        # Объединяем легенды
        lines_labels = [ax1.get_legend_handles_labels(), ax2.get_legend_handles_labels()]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        ax1.legend(lines, labels, loc='upper left')

        ax1.set_title('Требования к образованию')
        plt.xticks(rotation=45)
        plt.tight_layout()

        return self.fig_to_base64(fig)