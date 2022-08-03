import pygsheets
from os.path import join, dirname


def upload_row(data, file_title, sheet_title):
    worksheet = _get_worksheet(file_title, sheet_title)
    worksheet.append_table(values=data)


def _get_worksheet(file_title, sheet_title):
    # Authenticate this application with a Google account
    gc = pygsheets.authorize(service_file=join(dirname(__file__), 'drive.json'))
    file = gc.open(file_title)
    return file.worksheet_by_title(sheet_title)


def _check_available_rows(worksheet, active_rows, df_rows):
    worksheet_total_rows = worksheet.rows
    if worksheet_total_rows < (df_rows + active_rows + active_rows / 10):
        worksheet.add_rows(int(worksheet_total_rows / 4))
