import io
import base64
import matplotlib
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeRegressor, plot_tree

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


class AdvancedAnalyzer:
    def __init__(self, vacancies):
        self.vacancies = vacancies
        self.data = self.prepare_data()

    def perform_correlation_analysis(self):
        if len(self.data) < 5:
            return {'error': 'Недостаточно данных для корреляционного анализа. Минимум 10 записей.'}

        corr_matrix = self.data[['salary', 'experience', 'education', 'platform']].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0, square=True,
                    ax=ax, cbar_kws={"shrink": 0.8}, linewidths=1, linecolor='white')
        ax.set_title('Матрица корреляций', fontsize=16, fontweight='bold', pad=20)

        labels = ['Зарплата', 'Опыт работы', 'Образование', 'Платформа']
        ax.set_xticklabels(labels, fontsize=12, rotation=45, ha='right')
        ax.set_yticklabels(labels, fontsize=12, rotation=0)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        correlation_plot = base64.b64encode(image_png).decode('utf-8')
        plt.close()

        salary_correlations = {}
        for factor in ['experience', 'education', 'platform']:
            if factor in corr_matrix.index:
                correlation = corr_matrix.loc['salary', factor]
                salary_correlations[factor] = {
                    'correlation': correlation,
                    'strength': self.get_correlation_strength(abs(correlation)),
                    'direction': 'положительная' if correlation > 0 else 'отрицательная'}

        results = {
            'correlation_plot': correlation_plot, 'correlation_matrix': corr_matrix.to_dict(), 'salary_correlations': salary_correlations,'data_count': len(self.data)}
        return results

    def get_correlation_strength(self, r_value):
        abs_r = abs(r_value)
        if abs_r >= 0.7:
            return 'сильная'
        elif abs_r >= 0.3:
            return 'умеренная'
        elif abs_r >= 0.1:
            return 'слабая'
        else:
            return 'очень слабая'

    def prepare_data(self):
        data_list = []

        for vacancy in self.vacancies:
            if vacancy.salary:
                experience_mapping = {
                    'Без опыта': 0,
                    'От 1 года': 1,
                    'От 3 лет': 3,
                    'От 6 лет': 6,
                    'От 10 лет': 10
                }

                experience_num = experience_mapping.get(vacancy.experience, 0)

                education_mapping = {
                    ' ученая степень': 3,
                    ' высшее образование': 2,
                    ' среднее образование': 1,
                    ' среднее профессиональное образование': 1,
                    ' Не имеет значения': 0
                }

                education_num = education_mapping.get(vacancy.education, 0)

                platform_mapping = {
                    'HeadHunter': 0,
                    'SuperJob': 1,
                    'Rabota.ru': 2
                }

                platform_num = platform_mapping.get(vacancy.aggregator, 0)

                data_list.append({
                    'salary': vacancy.salary,
                    'experience': experience_num,
                    'education': education_num,
                    'platform': platform_num,
                    'experience_text': vacancy.experience,
                    'education_text': vacancy.education,
                    'platform_text': vacancy.aggregator,
                    'company': vacancy.company
                })

        return pd.DataFrame(data_list)

    def perform_regression_analysis(self):
        if len(self.data) < 10:
            return {'error': 'Недостаточно данных для регрессионного анализа'}

        X = self.data[['experience', 'education', 'platform']]
        y = self.data['salary']

        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()

        predictions = model.predict(X)

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        axes[0, 0].scatter(y, predictions, alpha=0.5)
        axes[0, 0].plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
        axes[0, 0].set_xlabel('Фактическая зарплата')
        axes[0, 0].set_ylabel('Предсказанная зарплата')
        axes[0, 0].set_title('Фактические vs Предсказанные значения')
        axes[0, 0].grid(True, alpha=0.3)

        residuals = y - predictions
        axes[0, 1].scatter(predictions, residuals, alpha=0.5)
        axes[0, 1].axhline(y=0, color='r', linestyle='--')
        axes[0, 1].set_xlabel('Предсказанные значения')
        axes[0, 1].set_ylabel('Остатки')
        axes[0, 1].set_title('Анализ остатков')
        axes[0, 1].grid(True, alpha=0.3)

        coefficients = model.params[1:]
        features = ['Опыт', 'Образование', 'Платформа']
        axes[1, 0].bar(features, coefficients)
        axes[1, 0].set_xlabel('Признаки')
        axes[1, 0].set_ylabel('Коэффициент')
        axes[1, 0].set_title('Важность признаков в регрессии')
        axes[1, 0].grid(True, alpha=0.3, axis='y')


        axes[1, 1].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
        axes[1, 1].set_xlabel('Остатки')
        axes[1, 1].set_ylabel('Частота')
        axes[1, 1].set_title('Распределение остатков')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        regression_plot = base64.b64encode(image_png).decode('utf-8')
        plt.close()

        results = {
            'regression_plot': regression_plot,
            'summary': str(model.summary()),
            'r_squared': model.rsquared,
            'adj_r_squared': model.rsquared_adj,
            'coefficients': model.params.to_dict(),
            'p_values': model.pvalues.to_dict(),

        }

        return results

    def analyze_decision_tree(self, max_depth=5, min_samples_split=10, min_samples_leaf=5):

        X = self.data[['experience', 'education', 'platform']]
        y = self.data['salary']


        le = LabelEncoder()
        X_encoded = X.copy()


        X_encoded['experience_text'] = self.data['experience_text']
        X_encoded['education_text'] = self.data['education_text']
        X_encoded['platform_text'] = self.data['platform_text']


        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        tree_regressor = DecisionTreeRegressor(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=42
        )

        tree_regressor.fit(X_train, y_train)

        y_pred = tree_regressor.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        cv_scores = cross_val_score(tree_regressor, X, y, cv=5, scoring='r2')
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()

        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': tree_regressor.feature_importances_
        }).sort_values('importance', ascending=False)

        plt.figure(figsize=(20, 10))
        plot_tree(
            tree_regressor,
            feature_names=['Опыт (годы)', 'Образование (уровень)', 'Платформа (код)'],
            filled=True,
            rounded=True,
            fontsize=10,
            max_depth=3,
            proportion=True
        )
        plt.title(f'Дерево решений для прогнозирования зарплаты\nМаксимальная глубина: {max_depth}',
                  fontsize=16, fontweight='bold', pad=20)


        buffer_tree = io.BytesIO()
        plt.savefig(buffer_tree, format='png', dpi=150, bbox_inches='tight')
        buffer_tree.seek(0)
        tree_image = base64.b64encode(buffer_tree.getvalue()).decode('utf-8')
        buffer_tree.close()
        plt.close()

        plt.figure(figsize=(10, 6))
        bars = plt.barh(feature_importance['feature'], feature_importance['importance'])
        plt.xlabel('Важность признака', fontsize=12)
        plt.title('Важность признаков в дереве решений', fontsize=14, fontweight='bold')
        for i, (bar, importance) in enumerate(zip(bars, feature_importance['importance'])):
            plt.text(importance + 0.01, bar.get_y() + bar.get_height() / 2,
                     f'{importance:.3f}',
                     va='center', fontsize=10)

        plt.gca().invert_yaxis()
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        buffer_importance = io.BytesIO()
        plt.savefig(buffer_importance, format='png', dpi=120, bbox_inches='tight')
        buffer_importance.seek(0)
        importance_image = base64.b64encode(buffer_importance.getvalue()).decode('utf-8')
        buffer_importance.close()
        plt.close()

        plt.figure(figsize=(10, 8))

        plt.subplot(2, 1, 1)
        plt.scatter(y_test, y_pred, alpha=0.6, edgecolors='w', linewidth=0.5)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()],
                 'r--', lw=2, label='Идеальная предсказательная линия')
        plt.xlabel('Фактическая зарплата (руб.)', fontsize=12)
        plt.ylabel('Предсказанная зарплата (руб.)', fontsize=12)
        plt.title(f'Предсказание зарплаты деревом решений\nR² = {r2:.3f}, MAE = {mae:.0f} руб.',
                  fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.subplot(2, 1, 2)
        errors = y_test - y_pred
        plt.hist(errors, bins=30, edgecolor='black', alpha=0.7)
        plt.xlabel('Ошибка предсказания (руб.)', fontsize=12)
        plt.ylabel('Частота', fontsize=12)
        plt.title('Распределение ошибок предсказания', fontsize=14, fontweight='bold')
        plt.axvline(x=0, color='r', linestyle='--', label='Нулевая ошибка')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        buffer_performance = io.BytesIO()
        plt.savefig(buffer_performance, format='png', dpi=120, bbox_inches='tight')
        buffer_performance.seek(0)
        performance_image = base64.b64encode(buffer_performance.getvalue()).decode('utf-8')
        buffer_performance.close()
        plt.close()

        sample_predictions = []
        sample_indices = np.random.choice(range(len(X_test)), min(5, len(X_test)), replace=False)

        for idx in sample_indices:
            actual = y_test.iloc[idx]
            predicted = y_pred[idx]
            error = actual - predicted


            exp_text = self.data.loc[y_test.index[idx], 'experience_text']
            edu_text = self.data.loc[y_test.index[idx], 'education_text']
            plat_text = self.data.loc[y_test.index[idx], 'platform_text']

            sample_predictions.append({
                'experience': exp_text,
                'education': edu_text,
                'platform': plat_text,
                'actual_salary': int(actual),
                'predicted_salary': int(predicted),
                'error': int(error),
                'error_percent': abs(error / actual * 100) if actual > 0 else 0
            })


        results = {
            'decision_tree_plot': tree_image,
            'feature_importance_plot': importance_image,
            'performance_plot': performance_image,
            'model_metrics': {
                'r_squared': round(r2, 4),
                'adjusted_r_squared': None,
                'mean_squared_error': round(mse, 2),
                'mean_absolute_error': round(mae, 2),
                'cross_val_mean': round(cv_mean, 4),
                'cross_val_std': round(cv_std, 4)
            },

            'sample_predictions': sample_predictions,

            'tree_parameters': {
                'max_depth': max_depth,
                'min_samples_split': min_samples_split,
                'min_samples_leaf': min_samples_leaf,
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test),
                'total_samples': len(self.data)
            },
        }

        return results



    def get_feature_name(self, feature_code):
        feature_map = {
            'experience': 'Опыт работы',
            'education': 'Образование',
            'platform': 'Платформа',
            'experience_text': 'Опыт (текст)',
            'education_text': 'Образование (текст)',
            'platform_text': 'Платформа (текст)'
        }
        return feature_map.get(feature_code, feature_code)