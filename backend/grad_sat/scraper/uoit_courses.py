import json
import logging
import os
from random import uniform
import time
from collections import defaultdict

from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import bs4

from grad_sat.scraper.models import Model


class Scraper:
    def __init__(
        self,
        password: str = None,
        username: str = None,
        unique_session_id: str = None,
        cookie: str = None,
    ):
        load_dotenv()
        self.__cookie: str = cookie
        self.__unique_session_id: str = unique_session_id
        self.__student_id = username or os.environ["USERNAME"]
        self.__password = password or os.environ["PASSWORD"]
        # TODO: timestamps
        logging.getLogger().setLevel(logging.INFO)
        if not self.__cookie and not self.__unique_session_id:
            self.refresh_creds()

    def start_scrape(self):
        print("TODO: add")

    def get_courses(self, limit: int, offset: int) -> Model:
        # TODO: probably a better way to handle when these are invalidated
        term = 202501

        endpoint = (
            "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/searchResults?"
            f"txt_term={term}&"  # this might change, 202501 is Winter 2025
            "startDatepicker=&"
            "endDatepicker=&"
            f"uniqueSessionId={self.__unique_session_id}&"
            f"pageOffset={offset}&"
            f"pageMaxSize={limit}&"
            "sortColumn=subjectDescription&"
            "sortDirection=asc"
        )

        response = requests.post(url=endpoint, headers={"Cookie": self.__cookie})
        json_tmp = json.loads(response.text)
        self.__random_sleep()

        for i, course in enumerate(json_tmp["data"]):
            crn = int(course["courseReferenceNumber"])

            if bool(course["isSectionLinked"]):
                json_tmp["data"][i]["linkedSections"] = self.get_linked_sections(
                    term, crn
                )
                self.__random_sleep()

            json_tmp["data"][i]["prerequisites"] = self.get_prerequisites(term, crn)
            self.__random_sleep()
            json_tmp["data"][i]["restrictions"] = self.get_restrictions(term, crn)
            self.__random_sleep()
            json_tmp["data"][i]["corequisites"] = self.get_co_requisites(term, crn)

        tmp = Model.model_validate(json_tmp)
        logging.info("scraped %d courses", len(tmp.data))

        return tmp

    # TODO: the sleeps make this crazy slow
    def refresh_creds(self):
        logging.info("refreshing creds")
        cookie, unique_session_id = "", ""

        with sync_playwright() as playwright:
            chromium = playwright.chromium
            browser = chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            def set_cookie(req):
                nonlocal cookie
                headers: dict[str, str] = req.all_headers()

                if "cookie" in headers and headers["cookie"].startswith("JSESSIONID="):
                    cookie = headers["cookie"]

            # watch reqs for cookie we need
            page.on("request", set_cookie)

            # this redirects to SAML login
            initial_url = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/term/termSelection?mode=search&mepCode=UOIT"
            page.goto(initial_url)

            # login
            page.locator("#userNameInput").fill(self.__student_id)
            page.locator("#passwordInput").fill(self.__password)
            page.locator("#submitButton").click()

            # wait for load/redirect
            page.wait_for_timeout(2000)
            page.screenshot(path="3.jpg")

            def set_unique_session_id(request):
                nonlocal unique_session_id
                parsed_url = urlparse(request.url)
                query_strings = parse_qs(parsed_url.query)
                if "uniqueSessionId" in query_strings:
                    unique_session_id = query_strings["uniqueSessionId"][0]

            page.on("request", set_unique_session_id)
            page.screenshot(path="3.jpg")

            # Select a Term for Class Search
            page.locator("#select2-chosen-1").click()
            page.wait_for_timeout(2000)

            # choose first option
            page.get_by_text(text="Winter 2025").click()
            page.wait_for_timeout(2000)

            # for the session to exist we need to go to the next page or something?
            # or maybe it doesn't have perms?
            page.locator("#term-go").click()
            page.wait_for_timeout(2000)

            page.screenshot(path="auth-final.jpg")

            self.__cookie = cookie
            self.__unique_session_id = unique_session_id
            print(self.__cookie)
            print(self.__unique_session_id)

    def get_restrictions(
        self, term: int, course_reference_number: int
    ) -> dict[str, list[str]]:
        endpoint = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/getRestrictions"
        restrictions_html = self.__get_missing(
            url=endpoint, term=term, crn=course_reference_number
        )

        r_soup = BeautifulSoup(restrictions_html, features="html.parser")
        restrictions: dict[str, list[str]] = defaultdict(list)
        r_soup_spans: bs4.element.ResultSet = r_soup.find_all("span")

        current_constraint_type = ""
        for span in r_soup_spans:
            span: bs4.element.Tag
            if span.has_attr("class") and "detail-popup-indentation" in span.get(
                "class", []
            ):
                restrictions[current_constraint_type].append(span.text)
            elif span.has_attr("class") and "status-bold" in span.get("class", []):
                current_constraint_type = span.text

        return restrictions

    def get_prerequisites(self, term: int, course_reference_number: int):
        # I'm going to have to make a mini antlr file or something to parse
        # the returned string, so I can translate it into constraints easily
        endpoint = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/getSectionPrerequisites"
        pr_html = self.__get_missing(
            url=endpoint, term=term, crn=course_reference_number
        )

        pr_soup = BeautifulSoup(pr_html, features="html.parser")
        pr_soup_table = pr_soup.find("table")
        buf = ""
        if not pr_soup_table:
            return buf

        for td in pr_soup_table.find_all("td"):
            td: bs4.element.Tag
            buf += td.text + " "

        return " ".join(buf.split())

    def get_co_requisites(self, term: int, course_reference_number: int):
        endpoint = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/getCorequisites"
        # TODO: extract course codes (do this after everythings scraped into db, just add html for now)
        return self.__get_missing(url=endpoint, term=term, crn=course_reference_number)

    def get_linked_sections(
        self, term: int, course_reference_number: int
    ) -> dict[str, list[int]]:
        endpoint = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/getLinkedSections"
        ls_html = self.__get_missing(
            url=endpoint, term=term, crn=course_reference_number
        )

        ls_soup = BeautifulSoup(ls_html, features="html.parser")
        ls_soup_table = ls_soup.find("table")

        options = defaultdict(list)
        # no pre-reqs
        if not ls_soup_table:
            return options

        pos, curr_option = 0, ""
        for td in ls_soup_table.find_all(["td"]):
            pos += 1
            td: bs4.element.Tag
            if "Option" in td.text:
                curr_option = td.text.strip()
                pos = 0

            if pos > 0 and pos % 4 == 0:
                options[curr_option].append(td.text)

        return options

    @staticmethod
    def __random_sleep():
        duration = uniform(0.05, 0.5)
        logging.info("sleeping for %s", duration)
        time.sleep(duration)

    def __get_missing(self, url: str, term: int, crn: int):
        response = requests.post(
            url,
            headers={
                "Cookie": self.__cookie,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data={"term": term, "courseReferenceNumber": crn},
        )

        return response.text
