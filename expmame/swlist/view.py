
def col_index_to_name(idx):
    from xlsxwriter.utility import xl_col_to_name
    column_name = xl_col_to_name(idx)
    return column_name + ":" + column_name

def df_to_excel(output_dir, prefix_file, source_df):
    from datetime import datetime
    from os import sep
    import pandas as pd
    sheet_name = prefix_file + "_swlist"
    xlsx_file = output_dir + sep + prefix_file + datetime.now().strftime("%Y%m%d") + ".xlsx"
    excel_writer = pd.ExcelWriter(xlsx_file, engine="xlsxwriter") # pylint: disable=abstract-class-instantiated
    source_df.to_excel(excel_writer, sheet_name=sheet_name, index=False, freeze_panes=(1,3))
    workbook = excel_writer.book
    worksheet = excel_writer.sheets[sheet_name]
    for column_idx, column_name in enumerate(source_df.columns.values):
        column_len = source_df[column_name].astype(str).str.len().max()
        column_len = max(column_len, len(column_name)) + 1
        worksheet.set_column(col_index_to_name(column_idx), column_len)

    excel_writer.save()
    return
