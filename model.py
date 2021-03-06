import concurrent.futures
import glob
import pickle
import time
from multiprocessing import Pool
import nltk

nltk.download('popular')
from joblib._multiprocessing_helpers import mp
from nltk import word_tokenize
import string
import numpy as np
from collections import OrderedDict
from prepare import download_material
from queryExpansion import query_expansion

download_material()


def load_cont(fld_path):  # give path of the folder containing all documents
    file_names = glob.glob(fld_path)
    contents = {}
    ori_cont = {}
    for file in file_names:
        file_name = file.split('/')
        file_name = file_name[-1]
        with open(file, 'r', encoding='utf-16') as f:
            data = f.read()
        contents[file_name] = data.lower()
        ori_cont[file_name] = data
    return contents, ori_cont


def remove_stopwords_and_punctuations_for_query(query):
    new_query = []
    with open('vn_stopword.txt', 'r', encoding='utf-8') as f:
        vietnamese_stop_words = f.read().split('\n')
    punctuations = list(string.punctuation) + ['\n']
    ignore_word = vietnamese_stop_words + punctuations
    for word in query:
        for w in word_tokenize(word):
            if w in ignore_word:
                continue
            else:
                new_query.append(w)
    return new_query


def remove_stopwords_and_punctuations(doc_dict):
    with open('vn_stopword.txt', 'r', encoding='utf-8') as f:
        vietnamese_stop_words = f.read().split('\n')
    punctuations = list(string.punctuation) + ['\n']
    ignore_word = vietnamese_stop_words + punctuations
    filtered_words_list = []
    for doc in doc_dict.values():
        for word in word_tokenize(doc.lower().strip()):
            if word in ignore_word:
                continue
            else:
                filtered_words_list.append(word)
    return filtered_words_list


def calc_tf_in_doc(vocab, doc_dict):
    tf_docs = {}
    for doc_id in doc_dict.keys():
        tf_docs[doc_id] = {}

    vocab_len = len(vocab)

    # Use multi-thread to accelerate process
    with concurrent.futures.ThreadPoolExecutor(max_workers=vocab_len) as executor:
        futures = []
        for word in vocab:
            futures.append(
                executor.submit(
                    assign_tf_docs(doc_dict, tf_docs, word)
                )
            )
    for future in concurrent.futures.as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(e)
    return tf_docs


def assign_tf_docs(doc_dict, tf_docs, word):
    for doc_id, doc in doc_dict.items():
        tf_docs[doc_id][word] = doc.count(word)


def calc_word_doc_fre(vocab, doc_dict):
    df = {}
    pool = Pool(mp.cpu_count())
    vocab_len = len(vocab)
    print("Total {} processes".format(vocab_len))
    for word in vocab:
        # Use multi-process to accelerate this step -> faster than n time(n is number cpu of computer) if compare with run on one process
        pool.apply_async(get_df_async, (doc_dict, word), callback=trigger_DF_callback)
    pool.close()
    pool.join()

    global df_callbacks
    for callback in df_callbacks:
        word, freq = callback
        df[word] = freq
    return df


df_callbacks = []


def trigger_DF_callback(df):
    global df_callbacks
    df_callbacks.append(df)


def get_df_async(doc_dict, word):
    frq = 0
    for doc in doc_dict.values():
        if word in word_tokenize(doc.lower().strip()):
            frq = frq + 1
    print('Done')
    return word, frq


def calc_idf(vocab, doc_fre, length):
    idf = {}
    for word in vocab:
        idf[word] = np.log10((length + 1) / doc_fre[word])
    return idf


def cal_tfidf(vocab, tf, idf_scr, doc_dict):
    tf_idf_list = {}
    for doc_name in doc_dict.keys():
        tf_idf_list[doc_name] = {}
    for word in vocab:
        for doc_name, doc in doc_dict.items():
            tf_idf_list[doc_name][word] = idf_scr[word] * tf[doc_name][word]
    return tf_idf_list


def process_query(query, doc_dict, tf_idf, limit):
    query_vocab = []
    for word in query.split():
        if word not in query_vocab:
            query_vocab.append(word)

    query_vocab = remove_stopwords_and_punctuations_for_query(query_vocab)
    extra_query = query_expansion(query_vocab)
    for word in query_vocab:
        if word in extra_query:
            extra_query.remove(word)
    query_vocab += extra_query
    query_word_count = {}
    for word in query_vocab:
        query_word_count[word] = query.lower().split().count(word)

    scores = {}
    for doc_name in doc_dict.keys():
        score = 0
        for word in query_vocab:
            try:
                score += query_word_count[word] * tf_idf[doc_name][word]
            except:
                if word not in extra_query:
                    # Penalizing
                    score -= len(doc_dict[doc_name]) * query_word_count[word]
        scores[doc_name] = score
        if score > 0 and doc_dict[doc_name].find(query) > 0:
            scores[doc_name] += 100000
    relevance_scores = {}
    quantity = 0
    for score in scores.items():
        if score[1] > 0:
            quantity += 1
            relevance_scores[score[0]] = score[1]

    ranks = OrderedDict(
        sorted(relevance_scores.items(),
               key=lambda dic: dic[1],
               reverse=True)
    )
    data = {k: ranks[k] for k in list(ranks)[:limit]}
    return data, quantity


docs = {}
tf_idf = []
ori_docs = []


def search(query, limit):
    start = time.time()
    try:
        global docs
        global ori_docs
        global tf_idf
        if len(docs) == 0 or len(ori_docs) == 0 or len(tf_idf) == 0:
            print("Get cached model")
            with open('cache/docs.txt', 'rb') as docs_bin:
                ori_docs = pickle.load(docs_bin)
            with open('cache/tf_idf.txt', 'rb') as tf_idf_bin:
                tf_idf = pickle.load(tf_idf_bin)
            for doc in ori_docs:
                docs[doc] = ori_docs[doc].lower()
    except Exception as e:
        print(e)
        print('Begin build model', time.time())
        path = 'Data/*.txt'
        docs, ori_docs = load_cont(path)
        data_len = len(docs)
        word_list = remove_stopwords_and_punctuations(docs)
        print('Step 1 done', time.time())
        vocab = list(set(word_list))
        tf_dict = calc_tf_in_doc(vocab, docs)
        print('Step 2 done', time.time())
        df_dict = calc_word_doc_fre(vocab, docs)
        print('Step 3 done', time.time())
        idf_dict = calc_idf(vocab, df_dict, data_len)
        print('Step 4 done', time.time())
        tf_idf = cal_tfidf(vocab, tf_dict, idf_dict, docs)
        print('Step 5 done', time.time())
        with open('cache/docs.txt', 'wb') as docs_bin:
            pickle.dump(docs, docs_bin)
        with open('cache/ori_docs.txt', 'wb') as docs_bin:
            pickle.dump(ori_docs, docs_bin)
        with open('cache/tf_idf.txt', 'wb') as tf_idf_bin:
            pickle.dump(tf_idf, tf_idf_bin)
        print('Finish build model', time.time())

    query = query.lower().strip()
    results, quantity = process_query(query, docs, tf_idf, limit)  # using Vector Space Model

    data = [ori_docs[file_name] for file_name in results]
    end = time.time()
    query_time = end - start
    print('Time:', query_time)
    print('quantity:', quantity)
    return data, query_time, quantity


# Debugging
if __name__ == "__main__":
    query = "n???n t???ng"
    data, time, quatity = search(query, 3)

    top = 0
    for i in data:
        top += 1
        print('Top', top, ":", i)
