#!/usr/bin/env python3
"""Search sentences searcher

Usage:
    tatoeba_search.py [--audio] [--username <username>] [--password <password] [--from <language>] [--to <language>] [--first-page <number>] [--last-page <number>] [--list <name>] <phrase>...

Options:
    -a, --audio                           Search with audio only.
    -u <username>, --username <username>  Username.
    -p <password>, --password <password>  Password.
    -f <language>, --from <language>      Language of source phrase.
    -t <language>, --to <language>        Language of target phrase.
    -b <number>, --first-page <number>    Start from the page with number <number>. [Default: 1]
    -e <number>, --last-page <number>     Finish at the page with number <number>.
    -l <name>, --list <name>              Save to the list with name <name>.
"""


from datetime import datetime
from docopt import docopt
from splinter import Browser
from time import sleep
import selenium
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def wait(check_function):
    start_time = datetime.now()
    while (not check_function()) and ((datetime.now() - start_time).seconds < 8):
        sleep(1)
    result = check_function()
    if result:
        return result
    else:
        raise Exception('Failed to load the page')


def login(browser, username, password):
    browser.click_link_by_text('Log in')
    browser.fill(name='data[User][username]', value=username)
    browser.fill(name='data[User][password]', value=password)
    browser.find_by_value('Log in')[0].click()
    wait(lambda: browser.is_element_visible_by_xpath('//*[@id="profile"]/a'))


def nothing_was_found(browser):
    return 'No results found for: ' in browser.html


def results_page_loaded(browser):
    current_page_css = '#main_content > div > div:nth-child(2) > span > span.current.pageNumber'
    return (nothing_was_found(browser)
            or (browser.is_element_visible_by_css(current_page_css) and
                browser.find_by_css(current_page_css)[0].text)
            or browser.is_element_visible_by_css('.addToList'))


def search(browser, phrase, language_from, language_to, with_audio):
    browser.click_link_by_text('Advanced search')
    wait(lambda: browser.is_element_present_by_xpath('//*[@id="main_content"]/div/h2[text() = "Advanced search"]'))
    sleep(browser.wait_time)
    browser.find_by_id('AdvancedSearchQuery').fill(phrase)
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchFrom"]//*[@value="{language_from}"]')[0].click()
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchTo"]//*[@value="{language_to}"]')[0].click()
    if with_audio:
        browser.find_by_id('AdvancedSearchHasAudio')[0].select_by_text('Yes')
    [search for search in browser.find_by_text('Advanced search')
     if search.tag_name == 'button'][0].click()
    wait(lambda: results_page_loaded(browser))


def add_all_sentences_from_the_page(browser, list_name):
    if nothing_was_found(browser):
        return

    for show_add_to_list_button_button in browser.find_by_css('.addToList'):
        show_add_to_list_button_button.click()
        list_name_xpath = f'//*[contains(@class, "listOfLists")]//*[text()="{list_name}"]'
        [list_name_combobox
         for list_name_combobox in browser.find_by_xpath(list_name_xpath)
         if list_name_combobox.visible][0].click()
        [add_to_list_button
         for add_to_list_button in browser.find_by_css('.validateButton')
         if add_to_list_button.visible][0].click()
        show_add_to_list_button_button.click()


def add_all_sentences(browser, first_page, last_page, list_name):
    loaded_page, page = wait(lambda: results_page_loaded(browser)), 1
    if page >= first_page:
        logging.info(f'Page {page}')
        add_all_sentences_from_the_page(browser=browser, list_name=list_name)
    next_button = browser.find_by_css('.next')
    while (next_button) and (last_page is not None) and (page < last_page):
        page += 1
        next_button[0].click()
        while loaded_page != str(page):
            loaded_page = wait(lambda: results_page_loaded(browser))
        next_button = browser.find_by_css('.next')
        if page >= first_page:
            logging.info(f'Page {page}')
            add_all_sentences_from_the_page(browser=browser, list_name=list_name)


def main(args):
    with Browser() as browser:
        browser.visit('https://tatoeba.org/eng')
        try:
            last_page = int(args['--last-page'])
        except TypeError:
            last_page = None
        login(
            browser=browser,
            username=args['--username'],
            password=args['--password'])
        for phrase in args['<phrase>']:
            added = False
            while not added:
                logging.info(f'{phrase}:')
                try:
                    search(
                        browser=browser,
                        phrase=phrase,
                        language_from=args['--from'],
                        language_to=args['--to'],
                        with_audio=(args['--audio'] is not None))
                    add_all_sentences(
                        browser=browser,
                        first_page=int(args['--first-page']),
                        last_page=last_page,
                        list_name=args['--list'])
                    added = True
                except Exception as e:
                    logging.info(str(e))


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)

