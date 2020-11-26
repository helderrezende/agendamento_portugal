import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_concelhos_name(id_concelho):
    link = 'https://agendamento.irn.mj.pt/steps/get_concelhos.php?id_distrito={0}'.format(str(id_concelho))
    result = requests.get(link)
    c = result.content
    soup = BeautifulSoup(c)

    options = soup.find_all('option')
    names = {x['value']: x.text for x in options}
    del names['']
    return names

def open_page_and_select_cc(query='cc'):
    DRIVER_PATH = 'data/chromedriver'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    driver.get('https://agendamento.irn.mj.pt/steps/step1.php')


    select_servico = Select(driver.find_element_by_xpath('//*[@id="servico"]'))
    if query == 'cc':
        select_servico.select_by_visible_text('Pedido / Renovação de Cartão de Cidadão')
        delay = 1
        button = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="myModal"]/div/div/div[3]/button'))).click()
        
    elif query == 'passport':
        select_servico.select_by_visible_text('Pedido de Passaporte Electrónico')
        
    else:
        print ("query is cc or passport")


    return driver
    

def get_distritos_names():
    driver = open_page_and_select_cc()
    html_source = driver.page_source
    soup = BeautifulSoup(html_source)
    
    distritos = soup.find_all('select')[1].find_all('option')
    names = {x.text: x['value'] for x in distritos}
    del names['Selecione uma opção']
    
    driver.close()
    return names


def is_validated(distrito, concelho):
    today = pd.to_datetime('today').strftime("%Y-%m-%d")
    
    link = 'https://agendamento.irn.mj.pt/steps/get_aval.php?f=checkStep1&ids={0}&idc={1}&data={2}&sab=0'.format(str(distrito),
                                                                                                             str(concelho),
                                                                                                             str(today))
    
    result = requests.get(link)
    c = result.content
    soup = BeautifulSoup(c)
    
    return soup.text

def get_hours(distritos, query='cc'):
    from selenium.webdriver.support.ui import Select
    
    driver = open_page_and_select_cc(query)
    distrito_dict = get_distritos_names()
    result = pd.DataFrame()
    for distrito in distritos:
        print ("Distrito: {0}".format(distrito))
        concelhos = get_concelhos_name(distrito_dict[distrito])
        select_distrito = Select(driver.find_element_by_xpath('//*[@id="distrito"]'))
        select_distrito.select_by_visible_text(distrito)
        
        for concelho_id in concelhos.keys():
            print ("Concelho: {0}".format(concelhos[concelho_id]))
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="concelho"]/option[2]')))
            select_concelho = Select(driver.find_element_by_xpath('//*[@id="concelho"]'))
            select_concelho.select_by_value(concelho_id)

            driver.find_element_by_xpath('//*[@id="btnSeguinte"]').click()
            
            try:
                new_page = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="divHorario"]/h4')))


                html_source = driver.page_source
                soup = BeautifulSoup(html_source)
                dates = soup.find_all('table')
                dates = [x.text[-10:] for x in dates]

                if len(dates) >= 1:
                    table_row = pd.DataFrame(columns=['dates', 'distrito', 'concelho'])
                    table_row['dates'] = dates
                    table_row['distrito'] = distrito
                    table_row['concelho'] = concelhos[concelho_id]

                    result = pd.concat([result, table_row])

                driver.find_element_by_xpath('//*[@id="divHorario"]/button[1]').click()
            except:
                print ("Error")
                button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="myModal_1"]/div/div/div[3]/button'))).click()

            
    driver.close()
    result = result.sort_values('dates')
    
    return result