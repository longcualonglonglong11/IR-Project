import time

from nltk.corpus import wordnet as wn


def query_expansion(query):
    start = time.time()
    query_expansion_list = []
    for q in query:
        synsets = wn.synsets(q)

        for synset in synsets:
            for word in synset._lemma_names:
                if word not in query_expansion_list:
                    query_expansion_list.append(word)
    end = time.time()
    print("query_expansion, time: ", end - start, "extra word:", len(query_expansion_list))
    return query_expansion_list
