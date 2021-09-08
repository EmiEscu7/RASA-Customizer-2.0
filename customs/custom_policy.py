import csv
from math import sqrt
from typing import Optional, Any, Dict, List, Text


from rasa.shared.core.domain import Domain

from rasa.core.featurizers.tracker_featurizers import (
    TrackerFeaturizer
)
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter
from rasa.core.policies.policy import Policy, PolicyPrediction
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.generator import TrackerWithCachedStates
from rasa.shared.utils.io import is_logging_disabled
from rasa.core.constants import MEMOIZATION_POLICY_PRIORITY

from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY




# temporary constants to support back compatibility
MAX_HISTORY_NOT_SET = -1
OLD_DEFAULT_MAX_HISTORY = 5

class PersonalityPolicy(Policy):

    def __init__(
        self,
        featurizer: Optional[TrackerFeaturizer] = None,
        priority: int = MEMOIZATION_POLICY_PRIORITY,
        answered: Optional[bool] = None,
        **kwargs: Any,
        ) -> None:
        super().__init__(featurizer, priority, **kwargs)
        self.answered = False
        
    def train(
        self,
        training_trackers: List[TrackerWithCachedStates],
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> None:
        """Trains the policy on given training trackers.
        Args:
            training_trackers:
                the list of the :class:`rasa.core.trackers.DialogueStateTracker`
            domain: the :class:`rasa.shared.core.domain.Domain`
            interpreter: Interpreter which can be used by the polices for featurization.
        """
        pass

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> PolicyPrediction:    

        sender_id = tracker.current_state()['sender_id']
        
        personality = self.get_personality(tracker)
        rta = self.generator_message(tracker, personality)
        
        if(self.answered):
            result = confidence_scores_for('action_listen', 1.0, domain)
            self.answered = False
        else:
            result = confidence_scores_for(rta, 1.0, domain)
            self.answered = True

        return self._prediction(result)



    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "scrum_master_policy.json"

    def get_personality(self, tracker:DialogueStateTracker):
        var = tracker.current_state()["latest_message"]
        metadata = var["metadata"]
        personality = metadata["personality"]
        return personality

    def generator_message(self, tracker: DialogueStateTracker, personality, sender = None):
        rta = ''
        intent = tracker.latest_message.intent.get(INTENT_NAME_KEY) 
        if(intent != "out_of_scope"): 
            style_answer = self.get_style_answer(personality)
            rta = 'utter_'
            rta += intent + style_answer
        return rta        

    def get_style_answer(self, personality:dict) -> Text:  
        
        """ 
            Este metodo agarra los valores de cada atributo del diccionario pasado por parametro y en base a ellos, busca que perfil tiene mas similitud con ellos.

            Retorna: Un tipo de respuesta en base a la personalidad (String)
        """
        vector_personalities = self.transform_dict_to_vector(personality)   
        neighbour = self.get_neighbour(vector_personalities) #obtiene a que vecindad se parece el vector
        #neighbour = [nro,[vector_personality]]
        #vector_personality = [nro,nro,nro,nro,nro,"_formal"] -> ejemplo
        vector = neighbour[-1] # -> esto da el vector_personality
        return vector[-1] #retorna si era "_formal" ó "_comun" ó "_informal"


    def get_priority_mood(self):
        """
            ----------SIN USO ACTUALMENTE----------
            La idea de esta funcion es que un algoritmo de machine learning determine
            la importancia que se le deba dar a c/u de los parametros que definen el 
            estado de animo de una persona. Actualmente devolvemos un vector con unos
            pesos determinados, que modelan los valores esperados del algoritmo
        """
        # pesos asignados a cada dimensión. 
        return [2, 1.5, 1, 1.5, 2]
    
    def get_neighbour(self, input:list) -> list:
        """
            Este algoritmo obtiene la distancia entre "input" y todos los vectores de familia
            Retorna: El menor de los tres vectores calculado, exactamente retornará: [dist_min, vector_personality]
            vector_personality = [nro,nro,nro,nro,nro,"_formal"] -> ejemplo
        
        """
               
        min_dist_formal = self.compare_to_neighbour(input,"_formal")
        min_dist_informal = self.compare_to_neighbour(input,"_informal")
        min_dist_comun = self.compare_to_neighbour(input,"_comun")
        return (min(min_dist_comun,min_dist_formal,min_dist_informal))

    def compare_to_neighbour(self,vector_input:list, neighbour: Text) -> list:
        """
         Compara el vector_input con la vecindad en particular, retornando
         la distancia que hay a tal vecindad.
         Una vecindad se compone de vectores que definen la vecindad.
         Output: [distancia,vector+similar]
        """
        dataframe_examples = self.get_examples_personalities_values()
        min_vector = dataframe_examples[0] #el primero del dataframe
        min_dist = 0
        cant = 0

        for example in dataframe_examples: #example = [1,1,1,1,1,STRING]
            if( example[-1] == neighbour ):
                example_no_string = example[:-1] #quita el string
                dist_actual = self.dist_euclidea(vector_input,example_no_string)
                if(min_dist < dist_actual):
                    min_vector = example
                min_dist += dist_actual
                cant+=1

        return [(min_dist/cant),min_vector]

    def get_examples_personalities_values(self) -> list:
        """
         Lee el archivo .csv y lo transforma a una lista
         Excluye la primer row que es la que contiene el 
         "encabezado" del csv. ("NEUROTICISM";"EXTRAVERSION";"OPENNESS";"AGREEABLENESS";"CONSCIENTIOUSNESS";"STYLE")
        """
        conjunto = []
        example = []
        with open('examples_personalities.csv') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=';',quoting=csv.QUOTE_NONNUMERIC)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    #print(f'Estas son las columnas {", ".join(row)}')   Las columnas no son value
                    line_count += 1
                else:
                    for i in range(len(row)):
                        example.append(row[i])
                    conjunto.append(example)
                    example = []
        return conjunto

    def dist_euclidea(self,p:list,q:list) -> float:
        """
         Calcula la distancia euclídea tal como está definida en Python 3.8
         Pero como trabajamos con Python 3.7.9 no tenemos acceso a esa funcionalidad
         por lo que aquí está tal funcion
        """
        return sqrt(sum((px - qx) ** 2.0 for px, qx in zip(p, q)))

    def transform_dict_to_vector(self, dict: dict) -> list:
        """
         Transforma el diccionario en un vector ya que es importante
         el orden en que se genera el vector
        """
        vector = []
        vector.append(dict["Neuroticism"])
        vector.append(dict["Extraversion"])
        vector.append(dict["Openness"])
        vector.append(dict["Agreeableness"])
        vector.append(dict["Conscientiousness"])
        return vector