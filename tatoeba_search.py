#!/usr/bin/env python3
"""Search sentences searcher

Usage:
    tatoeba_search.py [--audio] [--username <username>] [--password <password] [--from <language>] [--to <language>] [--first-page <number>] [--list <name>] <phrase>...

Options:
    -a, --audio                           Search with audio only.
    -u <username>, --username <username>  Username.
    -p <password>, --password <password>  Password.
    -f <language>, --from <language>      Language of source phrase.
    -t <language>, --to <language>        Language of target phrase.
    -p <number>, --first-page <number>    Start from the page with number <number>. [Default: 1]
    -l <name>, --list <name>              Save to the list with name <name>.
"""


from docopt import docopt
from splinter import Browser
from time import sleep
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


url = 'https://tatoeba.org/eng'


def login(browser, username, password):
    browser.click_link_by_text('Log in')
    browser.fill(name='data[User][username]', value=username)
    browser.fill(name='data[User][password]', value=password)
    browser.find_by_value('Log in')[0].click()
    while not browser.is_element_visible_by_xpath('//*[@id="profile"]/a'): pass


def search(browser, phrase, language_from, language_to, with_audio):
    browser.click_link_by_text('Advanced search')
    while browser.is_element_present_by_xpath('//*[contains(@class, "sentence-and-translations")]'): pass
    browser.find_by_id('AdvancedSearchQuery').fill(phrase)
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchFrom"]//*[@value="{language_from}"]')[0].click()
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchTo"]//*[@value="{language_to}"]')[0].click()
    if with_audio:
        browser.find_by_id('AdvancedSearchHasAudio')[0].select_by_text('Yes')
    [search for search in browser.find_by_text('Advanced search')
     if search.tag_name == 'button'][0].click()


def add_all_sentences_from_the_page(browser, list_name):
    def no_results():
        return 'No results found for: ' in browser.html

    while not browser.is_element_visible_by_xpath('//*[@id="AdvancedSearchSearchForm"]'): pass
    while not (no_results() or browser.is_element_visible_by_css('.addToList')): pass
    if no_results():
        return
    for show_add_to_list_button_button in browser.find_by_css('.addToList'):
        show_add_to_list_button_button.click()

    list_name_xpath = f'//*[contains(@class, "listOfLists")]//*[text()="{list_name}"]'
    while not browser.is_element_visible_by_xpath(list_name_xpath): pass
    for list_name_combobox in browser.find_by_xpath(list_name_xpath):
        list_name_combobox.click()

    while not browser.is_element_visible_by_css('.validateButton'): pass
    for add_to_list_button in browser.find_by_css('.validateButton'):
        add_to_list_button.click()


def add_all_sentences(browser, first_page, list_name):
    while not browser.is_element_visible_by_xpath('//*[@id="AdvancedSearchQuery"]'): pass
    loaded_page, page = None, 1
    if page >= first_page:
        logging.info(f'Page {page}')
        add_all_sentences_from_the_page(browser=browser, list_name=list_name)
    next_button = browser.find_by_css('.next')
    while next_button:
        page += 1
        next_button[0].click()
        current_page_css = '#main_content > div > div:nth-child(2) > span > span.current.pageNumber'
        while loaded_page != str(page):
            page_loaded = False
            while not page_loaded:
                try:
                    page_loaded = browser.is_element_visible_by_css(current_page_css)
                    loaded_page = browser.find_by_css(current_page_css)[0].text
                except:
                    pass
        next_button = browser.find_by_css('.next')
        if page >= first_page:
            logging.info(f'Page {page}')
            add_all_sentences_from_the_page(browser=browser, list_name=list_name)


def main(args):
    with Browser() as browser:
        browser.visit(url)
        login(
            browser=browser,
            username=args['--username'],
            password=args['--password'])
        for phrase in args['<phrase>']:
            logging.info(f'{phrase}:')
            search(
                browser=browser,
                phrase=phrase,
                language_from=args['--from'],
                language_to=args['--to'],
                with_audio=(args['--audio'] is not None))
            add_all_sentences(
                browser=browser,
                first_page=int(args['--first-page']),
                list_name=args['--list'])


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)

