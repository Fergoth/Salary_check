import requests
from itertools import count
from dotenv import load_dotenv
import os
from terminaltables import SingleTable


def get_hh_vacancies_by_language(language, page=0):
    URL = "https://api.hh.ru/vacancies"
    programmer_id = 96
    moskow_hh_id = 1
    params = {
        "professional_role": programmer_id,
        "page": page,
        "per_page": 100,
        "area": moskow_hh_id,
        "period": 30,
        "text": language,
        "only_with_salary": True,
    }
    response = requests.get(URL, params=params)
    response.raise_for_status()
    return response.json()


def predict_salary(top, bot):
    coef_only_top = 0.8
    coef_only_bot = 1.2
    if top and bot:
        return (top + bot) // 2
    elif top:
        return int(top * coef_only_top)
    elif bot:
        return int(bot * coef_only_bot)
    return None


def predict_rub_salary_hh(vacancy):
    if vacancy["salary"]["currency"] != "RUR":
        return None
    return predict_salary(
        vacancy["salary"]["from"],
        vacancy["salary"]["to"],
    )


def fetch_vacancies_hh(lang):
    all_vacancies = []
    for page in count():
        vacancies = get_hh_vacancies_by_language(lang, page)
        if page > vacancies["pages"]:
            break
        all_vacancies += vacancies['items']
    return all_vacancies, vacancies['found']


def get_sj_vacancies_by_language(language: str, sj_token: str, page: int = 0):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": sj_token}
    moskow_sj_id = 4
    params = {
        "keyword": f"{language}",
        "town": moskow_sj_id,
        "page": page
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(vacancy):
    if vacancy["currency"] != "rub":
        return None
    return predict_salary(vacancy["payment_from"], vacancy["payment_to"])


def get_all_vacancies_sj(lang, token):
    for page in count():
        vacancies_page = get_sj_vacancies_by_language(lang, token, page)
        yield vacancies_page
        if not vacancies_page["more"]:
            break


def get_stats_vacancies_sj(languages, token):
    stat_all_languages_sj = {}
    for lang in languages:
        average_salary = 0
        proceded_vacancies = []
        for vacancy_response in get_all_vacancies_sj(lang, token):
            vacancies_page = vacancy_response["objects"]
            for vacancy in vacancies_page:
                predicted_salary = predict_rub_salary_sj(vacancy)
                if predicted_salary:
                    proceded_vacancies.append(predicted_salary)
        if len(proceded_vacancies):
            average_salary = sum(proceded_vacancies) // len(proceded_vacancies)
        stat_all_languages_sj[lang] = {
            "vacancies_found": vacancy_response["total"],
            "vacancies_processed": len(proceded_vacancies),
            "average_salary": average_salary
        }
    return stat_all_languages_sj


def get_stats_vacancies_hh(languages):
    stat_all_languages_hh = {}
    for lang in languages:
        average_salary = 0
        proceded_vacancies = []
        vacancies, vacancies_count = fetch_vacancies_hh(lang)
        for vacancy in vacancies:
            predicted_salary = predict_rub_salary_hh(vacancy)
            if predicted_salary:
                proceded_vacancies.append(predicted_salary)
        if len(proceded_vacancies):
            average_salary = sum(
                proceded_vacancies
            ) // len(proceded_vacancies)
        stat_all_languages_hh[lang] = {
            "vacancies_found": vacancies_count,
            "vacancies_processed": len(proceded_vacancies),
            "average_salary": average_salary
        }
    return stat_all_languages_hh


def print_table(stat, title):
    table = [
        [
            lang,
            stat[lang]["vacancies_found"],
            stat[lang]["vacancies_processed"],
            stat[lang]["average_salary"],
        ]
        for lang in stat.keys()
    ]
    table = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий Обработано",
            "Средняя зп",
        ],
    ] + table
    table_instance = SingleTable(table, title)
    table_instance.justify_columns[2] = "right"
    print(table_instance.table)


def main():
    load_dotenv()
    token = os.getenv("SUPERJOB_API_KEY")
    languages = [
        "python",
        "java",
        "javascript",
        "c#",
        "c++",
        "PHP",
        "TYPESCRIPT",
        "Rust",
        "Swift",
        "GO",
        "Kotlin",
    ]

    stat_sj = get_stats_vacancies_sj(languages, token)
    print_table(stat_sj, "Москва Вакансии SuperJob")
    print()
    stat_hh = get_stats_vacancies_hh(languages)
    print_table(stat_hh, "Москва Вакансии headhunter")


if __name__ == "__main__":
    main()
