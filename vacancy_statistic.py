import requests
from itertools import count
from dotenv import load_dotenv
import os
from terminaltables import SingleTable


def get_hh_vacancies_by_language(language, page=0):
    URL = "https://api.hh.ru/vacancies"
    params = {
        "professional_role": 96,
        "page": page,
        "per_page": 100,
        "area": 1,
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
    for page in count():
        vacancies = get_hh_vacancies_by_language(lang, page)
        if page > vacancies["pages"]:
            break
        yield vacancies["items"]


def get_all_vacancies_hh(lang):
    ans = []
    for vacancies in fetch_vacancies_hh(lang):
        ans += vacancies
    return ans


def get_sj_vacancies_by_language(language: str, sj_token: str, page: int = 0):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": sj_token}
    data = {"keyword": f"{language}", "town": 4, "page": page}
    response = requests.get(url, headers=headers, params=data)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(vacancy):
    if vacancy["currency"] != "rub":
        return None
    return predict_salary(vacancy["payment_from"], vacancy["payment_to"])


def get_all_vacancies_sj(lang, token):
    for page in count():
        vacancy = get_sj_vacancies_by_language(lang, token, page)
        yield vacancy["objects"]
        if not vacancy["more"]:
            break


def get_stats_vacancies_sj(languages, token):
    stat_all_languages_sj = {
        lang: {
            "vacancies_found": 0,
            "vacancies_processed": 0,
            "average_salary": 0
        } for lang in languages
    }
    for lang in languages:
        vacancies = get_sj_vacancies_by_language(lang, token)
        stat_all_languages_sj[lang]["vacancies_found"] = vacancies["total"]
        proceded_vacancies = []
        for vacancy_page in get_all_vacancies_sj(lang, token):
            for vacancy in vacancy_page:
                predict = predict_rub_salary_sj(vacancy)
                if predict:
                    proceded_vacancies.append(predict)
        stat_all_languages_sj[lang]["vacancies_processed"] = len(proceded_vacancies)
        if len(proceded_vacancies):
            stat_all_languages_sj[lang]["average_salary"] = sum(
                proceded_vacancies
            ) // len(proceded_vacancies)
    return stat_all_languages_sj


def get_stats_vacancies_hh(languages):
    stat_all_languages_hh = {
        lang: {
            "vacancies_found": 0,
            "vacancies_processed": 0,
            "average_salary": 0
        } for lang in languages
    }
    for lang in languages:
        vacancies = get_hh_vacancies_by_language(lang)
        stat_all_languages_hh[lang]["vacancies_found"] = vacancies["found"]
        proceded_vacancies = []
        for vacancy in get_all_vacancies_hh(lang):
            predict = predict_rub_salary_hh(vacancy)
            if predict:
                proceded_vacancies.append(predict)
        stat_all_languages_hh[lang]["vacancies_processed"] = len(proceded_vacancies)
        if len(proceded_vacancies):
            stat_all_languages_hh[lang]["average_salary"] = sum(
                proceded_vacancies
            ) // len(proceded_vacancies)
    return stat_all_languages_hh


def print_table(stat, title):
    TABLE_DATA = [
        [
            lang,
            stat[lang]["vacancies_found"],
            stat[lang]["vacancies_processed"],
            stat[lang]["average_salary"],
        ]
        for lang in stat.keys()
    ]
    TABLE_DATA = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий Обработано",
            "Средняя зп",
        ],
    ] + TABLE_DATA
    table_instance = SingleTable(TABLE_DATA, title)
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
