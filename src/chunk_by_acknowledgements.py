import os
import pickle
import traceback
import fitz
import concurrent.futures

def unstructure(pdf_name, languages=["chi_sim", "eng"], extract_images=False, header_threshold=50, footer_threshold=50):
    """
    从PDF文件的指定页面中提取文本，但排除页眉和页脚中的文本。

    此函数读取一个PDF文件，从每一页中提取文本，并根据提供的阈值过滤掉被认为是页眉或页脚的文本区域。

    参数:
        pdf_name (str): 需要处理的PDF文件的路径。
        languages (list[str], 可选): 考虑文本提取的语言列表，默认为["chi_sim", "eng"]。
        extract_images (bool, 可选): 是否需要提取图片。当前实现中未使用此参数，默认为False。
        header_threshold (int, 可选): 判断文本为页眉的像素高度阈值，默认为50。
        footer_threshold (int, 可选): 判断文本为页脚的像素高度阈值，默认为50。

    返回:
        list[str]: 从PDF文件中提取的文本块列表，不包括页眉和页脚中的文本。

    异常:
        Exception: 如果无法打开或处理PDF文件，将抛出异常，并提供错误信息。
    """
    text_list = []
    try:
        doc = fitz.open(pdf_name)
        for page in doc:
            page_height = page.rect.height
            text_blocks = page.get_text("blocks")
            text_blocks = sorted(text_blocks, key=lambda block: (block[1], block[0]))
            for block in text_blocks:
                y0, y1 = block[1], block[3]
                # 判断是否为页眉或页脚
                if y0 < header_threshold or y1 > page_height - footer_threshold:
                    continue
                text = block[4].strip()
                if text:
                    text_list.append(text)
        doc.close()
    except Exception as e:
        print(f"Error processing PDF {pdf_name}: {e}")
        traceback.print_exc()
        return []
    return text_list

def extract_acknowledgements(text_list):
    '''提取致谢部分，并只保留该部分后的第一个文本块'''
    acknowledgements = []
    ack_started = False
    end_keywords = ['references', 'bibliography', 'appendix', 'author contributions']
    title_keywords = ['acknowledgement', 'acknowledgment', 'acknowledgements', 'acknowledgments', 'acknowledges', 'thanks', 'funding']

    for i, text in enumerate(text_list):
        text_lower = text.lower().strip()

        # 检查行是否以任何关键词开始
        starts_with_keyword = any(text_lower.startswith(keyword) for keyword in title_keywords)

        # 检查大写字母的比例是否高
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        is_possible_title = len(text.split()) <= 5 and not text_lower.endswith('.') and uppercase_ratio > 0.5

        # 确认是否为标题行
        if starts_with_keyword or (is_possible_title and any(keyword in text_lower for keyword in title_keywords)):
            if not ack_started:
                ack_started = True
                acknowledgements.append(text)  # 将标题添加到结果中
            continue

        if ack_started:
            if any(keyword in text_lower for keyword in end_keywords):
                break  # 遇到结束关键词时停止

            if len(text.split()) <= 5:
                break
            acknowledgements.append(text)

    return acknowledgements

def process_pdf(file_path):
    file_name = os.path.basename(file_path)
    record_id = file_name.replace('.pdf', '')

    try:
        text_list = unstructure(pdf_name=file_path, languages=["eng"])
    except Exception as e:
        print(f"处理文件 {file_path} 时发生异常：{str(e)}")
        traceback.print_exc()

    debug_folder = "../esg_debug"
    with open(f"{debug_folder}/{record_id}_text_list.txt", "w", encoding="utf-8") as f:
        for text in text_list:
            f.write(text + "\n----------\n")

    acknowledgements = extract_acknowledgements(text_list)
    if acknowledgements:
        with open(f"../esg_pickle/{record_id}.pkl", "wb") as f:
            pickle.dump(acknowledgements, f)
        print(f"文本已保存至pickle：{record_id}.pkl")

        text_str = "\n----------\n".join(acknowledgements)
        with open(f"../esg_txt/{record_id}.txt", "w", encoding="utf-8") as f:
            f.write(text_str)
        print(f"文本已保存至txt文件：{record_id}.txt")
    else:
        print(f"未找到致谢部分：{file_path}")

if __name__ == '__main__':
    # 确保所有必要的文件夹存在
    required_folders = ["../esg_debug", "../esg_pickle", "../esg_txt"]
    for folder in required_folders:
        os.makedirs(folder, exist_ok=True)

    pdf_files = [f"../download/{file}" for file in os.listdir('../download') if file.endswith('.pdf')]
    print(f"发现{len(pdf_files)}个PDF文件，准备开始处理。")

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_pdf, pdf) for pdf in pdf_files]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"处理文件过程中发生错误：{str(e)}")