from ocirs.table_extraction.borderless_table_extraction import get_text_boxes, text_boxes_to_table
from ocirs.table_extraction.line_detector.line_detector import LineDetector


def get_bordered_table_OI(image, ocr_dataframe=None):

    text_boxes = get_text_boxes(image, ocr_dataframe)
    line_detector = LineDetector()
    horiz_lines, vert_lines = line_detector.detect_lines(image, text_boxes)
    print(horiz_lines)
    text_boxes = assign_rows(horiz_lines, text_boxes)
    text_boxes = assign_columns(vert_lines, text_boxes)
    table = text_boxes_to_table(text_boxes)
    print(type(table))

    return table 
    
def assign_rows(horiz_lines, text_boxes):
    row_ranges = list()
    for index, horiz_line in enumerate(horiz_lines[:len(horiz_lines) - 1]):
        x1, y1, x2, y2 = tuple(horiz_line)
        row_ranges.append((y1, horiz_lines[index + 1][1]))
    top_values = text_boxes["y2"].values.tolist()
    row_indexes = list()
    for top in top_values:
        for index, (min, max) in enumerate(row_ranges):
            if top <= max:
                row_indexes.append(index)
                break
        else:
            row_indexes.append(index)
    text_boxes["row"] = row_indexes
    return text_boxes
    
def assign_columns(vert_lines, text_boxes):
    column_ranges = list()
    for index, vert_line in enumerate(vert_lines[:len(vert_lines) - 1]):
        x1, y1, x2, y2 = tuple(vert_line)
        column_ranges.append((x1, vert_lines[index + 1][0]))
    left_values = text_boxes["x2"].values.tolist()
    column_indexes = list()
    for left in left_values:
        was_appended = False
        index = 0
        for index, (min, max) in enumerate(column_ranges):
            if left <= max:
                column_indexes.append(index)
                was_appended = True
                break
        if not was_appended:
            column_indexes.append(index)
    text_boxes["column"] = column_indexes
    return text_boxes