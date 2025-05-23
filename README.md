# ResumeAnalyzer
the model used to run the resume analyzer parsing pdf 

it uses spacy(with encore model), flask and pymupdf (the main libraries to be downloaded).
all the requirements can be fulfilled by downloading the requirements.txt file 

to download just type in the cmd ------>  pip install -r requirements.txt 
                                  |
                                  \
                                   ---------> python -m spacy download en_core_web_sm

                                   
NOTE: the file requirements.txt need be installed for the command to work
MAJOR_NOTE: requirements.txt also contains a name for encore model which is an extention of SpaCy so cannot be downloaded together.
remember to remove that name from requirement.txt locally after downloading if you intend to directly install the whole file using above given command
the second command in line is the download statement for encore model ---> run it after downloading requirements.txt

do put in the complete directory in place of requirements.txt if the terminal cannot locate the file

ERROR_ALERT : download process can throw a big error during installation of spacy library. this is because spacy is not compatible with the latest model of python 3.13 (unsure about .11 and .12) but it runs on python 3.10 >>>>>> in case of error check the version of python on the main user directory in cmd by using the command ---------> python --version

in this case you would need to either uninstall python 3.13 and install 3.10 (this means if you have downloaded any extra libraries you will have to download again)
--------------------------------------OR----------------------------------------------
download python 3.10 without uninstalling python 3.13 and set up a virtual environment parallel to the file that contains the code "resumeter.py" 
(look up instructions on chatgpt or youtube ) 
#chatgpt is personal recommendation
