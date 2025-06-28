import json
import os
import pygsheets


def authenticate_gsheets():
    # Authenticate using service account credentials from an environment variable or a file
    gc = pygsheets.authorize(service_account_env_var='GOOGLE_CREDENTIALS')  # Ensure GOOGLE_CREDENTIALS is set in your env
    return gc


def main():
    # Authenticate and write to Google Sheets
    gc = authenticate_gsheets()
    sheet_id = os.getenv('GOOGLE_SHEET_ID')  # Ensure GOOGLE_SHEET_ID is set in your env
    links_tab_name = os.getenv('LINKS_TAB_NAME') # Ensure LINKS_TAB_NAME is set in your env

    sheet = gc.open_by_key(sheet_id)

    print('the sheet: ', sheet)
    print('the tab name: ', links_tab_name)

    wks = sheet.worksheet_by_title(links_tab_name)

    print('wks: ', wks)
    
    repo_links = wks.get_col(1, include_tailing_empty=False)
    repo_shas = wks.get_col(2, include_tailing_empty=False)

    repo_details_list = []

    for idx, link in enumerate(repo_links):
        sha = repo_shas[idx]

        if sha is None:
            sha = ''

        repo_details_list.append(f'{link};{sha}')
    
    print('links: ', repo_links)
    print('shas: ', repo_shas)
    print('all details: ', repo_details_list)

    print(f"::set-output name=matrix::{repo_details_list}")

if __name__ == "__main__":
    main()