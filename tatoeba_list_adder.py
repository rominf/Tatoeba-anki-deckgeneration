#!/usr/bin/env python3
"""Tatoeba sentences finder

Usage:
    tatoeba_list_adder.py [--audio] [--username <username>] [--password <password] [--from <language>] [--to <language>] [--first-page <number>] <phrase>

Options:
    -a, --audio                           Search with audio only.
    -u <username>, --username <username>  Username.
    -p <password>, --password <password>  Password.
    -f <language>, --from <language>      Language of source phrase.
    -t <language>, --to <language>        Language of target phrase.
    -p <number>, --first-page <number>    Start from the page with number <number>. [Default: 1]
"""


from docopt import docopt
from splinter import Browser
from time import sleep


url = 'https://tatoeba.org/eng'


def login(browser, username, password):
    browser.click_link_by_text('Log in')
    browser.fill(name='data[User][username]', value=username)
    browser.fill(name='data[User][password]', value=password)
    browser.find_by_value('Log in')[0].click()
    while not browser.is_element_visible_by_xpath('//*[@id="profile"]/a'): pass


def search(browser, phrase, language_from, language_to, with_audio):
    browser.click_link_by_text('Advanced search')
    while not browser.is_element_visible_by_xpath('//*[@id="AdvancedSearchQuery"]'): pass
    browser.find_by_id('AdvancedSearchQuery').fill(phrase)
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchFrom"]//*[@value="{language_from}"]')[0].click()
    browser.find_by_xpath(
        f'//*[@id="AdvancedSearchTo"]//*[@value="{language_to}"]')[0].click()
    if with_audio:
        browser.find_by_id('AdvancedSearchHasAudio')[0].select_by_text('Yes')
    [search for search in browser.find_by_text('Advanced search')
     if search.tag_name == 'button'][0].click()


def add_all_sentences_from_the_page(browser):
    while not browser.is_element_visible_by_css('.addToList'): pass
    for show_add_to_list_button_button in browser.find_by_css('.addToList'):
        show_add_to_list_button_button.click()
    page_loaded = False
    while not browser.is_element_visible_by_css('.validateButton'): pass
    for add_to_list_button in browser.find_by_css('.validateButton'):
        add_to_list_button.click()


def add_all_sentences(browser, first_page):
    while not browser.is_element_visible_by_css('.next'): pass
    loaded_page, page = None, 1
    if page >= first_page:
        add_all_sentences_from_the_page(browser=browser)
    next_button = browser.find_by_css('.next')
    while next_button:
        print(f'Page {page}')
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
            add_all_sentences_from_the_page(browser=browser)


def main(args):
    with Browser() as browser:
        browser.visit(url)
        login(
            browser=browser,
            username=args['--username'],
            password=args['--password'])
        search(
            browser=browser,
            phrase=args['<phrase>'],
            language_from=args['--from'],
            language_to=args['--to'],
            with_audio=(args['--audio'] is not None))
        add_all_sentences(
            browser=browser,
            first_page=int(args['--first-page']))


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)

