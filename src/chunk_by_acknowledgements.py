import os
import pickle
import traceback
import fitz
import concurrent.futures

def unstructure(pdf_name, languages=["chi_sim", "eng"], extract_images=False):
    text_list = []
    try:
        doc = fitz.open(pdf_name)
        for page in doc:
            text_blocks = page.get_text("blocks")
            text_blocks = sorted(text_blocks, key=lambda block: (block[1], block[0]))
            for block in text_blocks:
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

        # 检查标题行的格式，判断是否为标题行
        is_possible_title = len(text.split()) <= 5 and not text_lower.endswith('.')

        # 检查当前行是否为致谢的标题行，启动提取
        if any(keyword in text_lower for keyword in title_keywords) and is_possible_title:
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
    os.makedirs(debug_folder, exist_ok=True)
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
    pdf_files = [f"../download/{file}" for file in os.listdir('../download') if file.endswith('.pdf')]
    print(f"发现{len(pdf_files)}个PDF文件，准备开始处理。")

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_pdf, pdf) for pdf in pdf_files]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"处理文件过程中发生错误：{str(e)}")
