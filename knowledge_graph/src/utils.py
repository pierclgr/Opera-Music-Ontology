class SituationCreator():
  def __init__(self, situa_type):
    self.situa_type = situa_type
    self.keyword_counter = {}

  def new(self, keyword):
    if keyword not in self.keyword_counter:
      self.keyword_counter[keyword] = 1
    else:
      self.keyword_counter[keyword] += 1
    return ("{}_{}_{}".format(keyword.lower().replace(" ", "_"),
                              self.situa_type,
                              str(self.keyword_counter[keyword]))).strip("_").title()
    
musical_instruments = ['Violin', 'Horn', 'Orchestra', 'Guitar', 'Viola', 'Cello', 'Quartet', 'Flute', 'Oboe', 'Organ', 'Harpsichord', 'Ensemble', 'Clarinet', 'Piano']
vocal_instruments = ['Alto', 'Baritone', 'Bass', 'Choir', 'Choral', 'Mezzo-Soprano', 'Soprano', 'Tenor']


def get_instrument_type_and_score(instrum:str):
  if instrum in vocal_instruments:
    instrum_type = "Voice"
  elif instrum in musical_instruments:
    instrum_type = "PhysicalInstrument"
  else:
    instrum_type = None

  # musical score
  if instrum_type is not None:
    if instrum_type == "Voice":
      score_type = "VocalScore"
    else:
      score_type = "InstrumentalScore"
  
  return instrum_type, score_type