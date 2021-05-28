import pandas as pd
import pytesseract
from scipy.cluster.hierarchy import fclusterdata
from ocirs.table_extraction.line_detector.line_detector import LineDetector

def get_borderless_table(image, ocr_dataframe=None):

    text_boxes = get_text_boxes(image, ocr_dataframe)
    text_boxes = assign_rows(text_boxes)
    text_boxes = assign_columns(text_boxes)
    text_boxes = split_columns_on_vert_lines(image, text_boxes)
    table = text_boxes_to_table(text_boxes)

    return table


def get_text_boxes(image, ocr_dataframe):

    OCR_TEXT_CONFIDENCE_THRESHOLD = 0.6 

    if ocr_dataframe is None:
        #If ocr_dataframe is not passed, will have to create the text box dataframe from scratch using pytesseract
        boxes = pytesseract.image_to_data(
            image, 
            output_type=pytesseract.Output.DICT,
            config=f"--oem 3 --psm 1"
        )
        boxes = pd.DataFrame.from_dict(boxes)
    
    else:
 
        boxes = ocr_dataframe.copy()

    boxes["conf"] = boxes["conf"].apply(lambda x: int(x))
    boxes = boxes[boxes.conf > OCR_TEXT_CONFIDENCE_THRESHOLD]
    boxes['text'] = boxes["text"].apply(lambda x: x.strip())
    boxes = boxes[boxes.text != ""]
    boxes.drop(["level", "page_num", "block_num", "par_num", "line_num", "word_num", "conf"], 
        axis=1, 
        inplace=True
    )
    boxes = boxes.reset_index(drop=True)


    if not boxes.empty:
        boxes["y_middle"] = boxes.apply(lambda row: row.top + int(row.height/2), axis=1)
        boxes["y2"] = boxes.apply(lambda row: row.top + row.height, axis=1)
        boxes["x_middle"] = boxes.apply(lambda row: row.left + int(row.width/2) , axis=1)
        boxes["x2"] = boxes.apply(lambda row: row.left + row.width, axis=1)

    return boxes

def assign_rows(text_boxes):
    max_dist_rows = 10
    row_indexes = get_clustering_indexes(
        text_boxes[["y_middle"]].values, 
        max_dist_rows
    )
    text_boxes["row"] = row_indexes
    return text_boxes

def assign_columns(text_boxes):
    max_dist_columns = 60
    columns_indexes = get_clustering_indexes(
        text_boxes[["x_middle"]].values, 
        max_dist_columns
    )
    text_boxes["column"] = columns_indexes
    return text_boxes


def get_clustering_indexes(list_data, max_distance):
    clusters = fclusterdata(list_data, t=max_distance, criterion='distance')
    clusters_with_list_data = dict()
    for index, cluster_number in enumerate(clusters):
        if not clusters_with_list_data.get(cluster_number):
            clusters_with_list_data[cluster_number] = list()
        clusters_with_list_data[cluster_number].append(list_data[index])
    clusters_to_indexes = dict()
    for index, (key, value) in enumerate(clusters_with_list_data.items()):
        clusters_to_indexes[key] = index
    indexes = [
        clusters_to_indexes[cluster_number] for cluster_number in clusters
    ]
    return indexes

def split_columns_on_vert_lines(image, text_boxes):
    line_detector = LineDetector()
    _, vert_lines = line_detector.detect_lines(image, text_boxes, "vertical")
    text_boxes_columns = [x for _, x in text_boxes.groupby("column")]
    for no, (x1, y1, x2, y2) in enumerate(vert_lines):
        for df_index, df in enumerate(text_boxes_columns):
            left = df["left"].min()
            right = df["x2"].max()
            if x1 > left and x1 <= right:
                for row_index, row in df.iterrows():
                    # if textbox is on right side of this line, then
                    # this textbox should be placed one column further (left to right)
                    if row.x2 >= x1:
                        text_boxes.loc['column', row.name] = row["column"] + no + 1
    return text_boxes

def text_boxes_to_table(text_boxes):
    text_boxes = aggregate_text_boxes(text_boxes)
    amount_rows = int(text_boxes["row"].max()) + 1
    amount_columns = int(text_boxes["column"].max()) + 1
    
    data = list()
    for i in range(amount_rows):
        row = list()
        for j in range(amount_columns):
            result = text_boxes.loc[
                (text_boxes["row"] == i) & 
                (text_boxes["column"] == j)
            ]
            if result.empty:
                row.append(None)
            else:
                row.append(result["text"].iloc[0].strip())
        data.append(row)
    table = pd.DataFrame(data=data[1:], columns=data[0])
    # table = table.dropna(axis=1, how='all')
    # table = table.dropna(axis=0, how='all')
    return table

def aggregate_text_boxes(text_boxes):
    grouped = [x for _, x in text_boxes.groupby(["column", "row"])]
    data = list()
    for df in grouped:
        df = df.reset_index(drop=True)
        left = df["left"][0]
        top = df["top"].min()
        width = df["width"].sum()
        height = df["height"].max()
        text = ""
        column = df["column"][0]
        row = df["row"][0]
        for index, element in df.iterrows():
            text += (" " + element["text"])
        data.append([left, top, width, height, text, row, column])
    # columns = df.columns.values.tolist()
    text_boxes_aggregated = pd.DataFrame(
        data=data,
        columns=["left", "top", "width", "height", "text", "row", "column"]
    )
    return text_boxes_aggregated