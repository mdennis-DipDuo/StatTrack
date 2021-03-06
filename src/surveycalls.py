from . import connect
import time
from random import choice
from string import ascii_uppercase

surveydb = connect.DBConnect('survey')
userdb = connect.DBConnect('users')

def postSurvey(questions,user):

    organized = {}
    idVal = (''.join(choice(ascii_uppercase) for i in range(5)))

    while surveydb.checkExists('_id', idVal):
        idVal = (''.join(choice(ascii_uppercase) for i in range(5)))

    user['surveys'].append(idVal);
    userdb.update(user['_id'],user);

    titleVal = questions['title']
    descVal = questions['description']
    q_count = questions['qCount']

    for q in questions['questions']:
        id = q.split('-')

        if id[0] in organized:
            organized[id[0]][id[1]] = questions['questions'][q]
        else:
            organized[id[0]] = { id[1]: questions['questions'][q] }

    resultsVal = []
    responsesVal = 0;
    startTime = time.time()
    duration = 7 * 24 * 60 * 60
    endTime = startTime + duration

    node = {
        'title':  titleVal,
        'desc':   descVal,
        'quesCount': q_count,
        'questions': organized,
        'results':  resultsVal,
        'responseCount': responsesVal,
        'start':    startTime,
        'duration': duration,
        'end':  endTime
    }

    temp = []
    for i in range(node['quesCount']):
        if node['questions']['q'+str(i)]['type'] == 'MC':
            node['questions']['q'+str(i)]['opt'] = []
            for x in range(4):
                if node['questions']['q'+str(i)]['opt'+str(x+1)] != "":
                    node['questions']['q'+str(i)]['opt'].append(node['questions']['q'+str(i)]['opt'+str(x+1)])
                node['questions']['q'+str(i)].pop('opt'+str(x+1))
        temp.append(node['questions']['q'+str(i)])

    node['questions'] = temp




    surveydb.update(idVal, node)
    return organized


def submitSurvey(submission,sID):
    global surveydb

    survey = surveydb.getDict('_id',sID)

    if survey['results'] == []:
        tempList = []
        for x in range(survey['quesCount']):
            temp = []
            if survey['questions'][x]['type'] == 'MC':
                for y in range(len(survey['questions'][x]['opt'])):
                    temp.append(0)
            elif survey['questions'][x]['type'] == 'TF':
                temp.append(0)
                temp.append(0)
            tempList.append(temp)
        survey['results'] = tempList
    for x in range(len(submission)):
        if survey['questions'][x]['type'] == 'MC':
            survey['results'][x][int(submission[x])] += 1
        elif survey['questions'][x]['type'] == 'TF':
            survey['results'][x][int(submission[x])] += 1
        elif survey['questions'][x]['type'] == 'R':
            survey['results'][x].append(int(submission[x]))
        elif survey['questions'][x]['type'] == 'N':
            survey['results'][x].append(int(submission[x]))

    survey['responseCount'] += 1

    surveydb.update(sID,survey)


def getSurveys(surveyList,standardize=None):
    total = { 'active': [], 'closed': [], 'overview': {}}
    total['overview']['totalP'] = 0
    total['overview']['totalS'] = len(surveyList)
    now = time.time()
    for sID in surveyList:
        survey = surveydb.getDict('_id',sID)
        closeTime = survey['start']+survey['duration']
        total['overview']['totalP'] += survey['responseCount']
        if closeTime >= now:
            total['active'].append({
                'opened': time.strftime('%m/%d/%Y %H:%M', time.localtime(survey['start'])),
                'title': survey['title'],
                'desc': survey['desc'],
                'questions': survey['questions'],
                'duration': survey['duration'],
                'closed': time.strftime('%m/%d/%Y %H:%M', time.localtime(closeTime)),
                'shareURL': survey['_id'],
                'rlen': survey['responseCount'],
                'results': survey['results'],
                'qlen': len(survey['questions'])
            })
            if len(surveyList) == 1 and not(standardize):
                return total['active'][0]
        else:
            total['closed'].append({
                'opened': time.strftime('%m/%d/%Y %H:%M', time.localtime(survey['start'])),
                'title': survey['title'],
                'desc': survey['desc'],
                'questions': survey['questions'],
                'duration': { 'epoch':survey['duration'], 'friendly': epoch2timespan(survey['duration'])},
                'closed': time.strftime('%m/%d/%Y %H:%M', time.localtime(closeTime)),
                'shareURL': survey['_id'],
                'rlen': survey['totalResponses'],
                'results': survey['results'],
                'qlen': len(survey['questions'])
            })
            if len(surveyList) == 1 and not(standardize):
                return total['closed'][0]
    if len(surveyList) == 0:
        total['overview']['avgP'] = '{0:.1f}'.format(0)
        return total

    avgP = total['overview']['totalP']/total['overview']['totalS']
    total['overview']['avgP'] = '{0:.1f}'.format(avgP)
    return total

def epoch2timespan(seconds):

    if seconds < 60:
        return str(seconds) + ' sec(s)'
    elif seconds < 60*60:
        return str(int(seconds/60)) + ' min(s)'
    elif seconds < 60*60*24:
        return str(int(seconds/60/24)) + ' hr(s)'
    elif seconds < 60*60*24*7:
        return str(int(seconds/60/24/7)) + ' day(s)'
    else:
        return str(int(seconds/60/24/52)) + ' Week(s)'
