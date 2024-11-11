import numpy as np
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.data.path.append("C://Users//lenovo//Desktop//teachtreckAI//roua")
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
print("aaaaaaaaaaaaaaaaaaaa",nltk.data.path)
def nltk_tokenize(text):
  return nltk.word_tokenize(text)
def remove_stopwords_nltk(text):
  stop_words= stopwords.words('french')
  stop_words.append('.')
  word_tokens=word_tokenize(text)
  filtered_sentence=[w for w in word_tokens if not w.lower() in stop_words]
  return filtered_sentence


#YOU MUST USE the provided data.csv as it was processed to remove extra commas in the responses
training_data = pd.read_csv("C://Users//lenovo//Desktop//teachtreckAI//roua//data.csv",encoding='utf-8')


#Calcul Combien des mots clé de la réponse correcte sont présents dans la réponse de l'utilisateur
#On tient compte STRICTEMENT de l'ordre des mots clé présents dans la reponse
def count_items_same_order(list1, list2):
    x=0
    a=0
    for i in range(len(list2)):
      if list2[i]==list1[x]:
        a+=1
        x+=1
    return a



def ask_random_question_and_evaluate(dataset, domaine):
    # Filter dataset by given 'Domaine'
    filtered_dataset = dataset[dataset['Domaine'] == domaine]
    score_tot=0
    print("Domaine = ",domaine)
    if filtered_dataset.empty:
        print(f"No questions available for the domain: {domaine}")
        return
    
    for _ in range(3):
        random_index = np.random.randint(0, len(filtered_dataset))
        random_question = filtered_dataset.iloc[random_index]

        question = random_question['Question']
        correct_response = random_question['RÃ©ponse correcte']

        print("Chatbot: ", question)
        user_response = input("User: ")

        print("User Response:", user_response)
        print("Correct Response:", correct_response)

        #Remove Stopwords
        user_response_keywords = remove_stopwords_nltk(user_response)
        correct_response_keywords = remove_stopwords_nltk(correct_response)

        print('Keywords in User Response : ',user_response_keywords)
        print('Keywords in Correct Response : ',correct_response_keywords)

        print('Matching Keywords : ',count_items_same_order(correct_response_keywords, user_response_keywords))
        matching_keywords = count_items_same_order(correct_response_keywords, user_response_keywords)
        score = float(matching_keywords) / len(correct_response_keywords)

        print("Chatbot Score: ",score)
        score_tot+=score

    #Affiche Score finale sur 3 Points
    print('Score Finale : ',score_tot,' / 3')


# Les domaines disponibles: Python niveau 1, Python (POO), Java (POO), Base de données, PL/SQL, IA, ML, DL, JavaScript, HTML, CSS
# dom=input("Entrez le domaine: ")
# ask_random_question_and_evaluate(training_data, dom)