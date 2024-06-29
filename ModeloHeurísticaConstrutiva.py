# Função para ler o arquivo
def read_file(filename):
    staff = {}
    days = {}
    shifts = []
    

    with open(filename, 'r') as file:
        section = None
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:  
                continue
            if line.startswith('SECTION_'):
                section = line
                continue
            
            if section == 'SECTION_HORIZON':
                horizon = int(line)
                days = {day: {} for day in range(0, horizon)}
               # print(days)
                
            elif section == 'SECTION_SHIFTS':
                shift_id, length_in_mins, cannot_follow = line.split(',')
                shifts.append(shift_id)

                for day in days:
                    days[day][shift_id] = {
                        'lengthInMins': int(length_in_mins),
                        'cannotFollow': cannot_follow.split('|') if cannot_follow else [],
                        'requirement' : [],
                        'weightUnder': [],
                        'weightOver': []
                    }

                #print(days)  

            elif section == 'SECTION_STAFF':
                 parts = line.split(',', 1)
                 employee_id = parts[0]
                 additional_parts = parts[1].split(',', 1)
                 existing_shifts = additional_parts[0].split('|')
                 
        
                 Max_TotalMinutes, Min_TotalMinutes, Max_ConsecutiveShifts, Min_ConsecutiveShifts, Min_ConsecutiveDaysOff, Max_Weekends = additional_parts[1].split(',')

                 staff[employee_id] = {
                    'shifts' : {},
                    'maxTotalMinutes': int(Max_TotalMinutes),
                    'minTotalMinutes': int(Min_TotalMinutes),
                    'maxConsecutiveShifts': int(Max_ConsecutiveShifts),
                    'minConsecutiveShifts': int(Min_ConsecutiveShifts),
                    'minConsecutiveDaysOff': int(Min_ConsecutiveDaysOff),
                    'maxWeekends': int(Max_Weekends),
                    'dayIndexesOFF': []        
                 }
                 
                 for shift_info in existing_shifts:
                     shift_id, Max_Shifts = shift_info.split('=')
                     staff[employee_id]['shifts'][shift_id] = {'maxShifts': int(Max_Shifts)}
                
                 
                 #print(shift_id)
                 #print(Max_Shifts)
                 #print(staff)   
                 

            elif section == 'SECTION_DAYS_OFF':
                parts = line.split(',', 1)
                employee_id = parts[0]
                day_indexes_str = parts[1]
                day_indexes_OFF = [int(index) for index in day_indexes_str.split(',')]
                
                if employee_id in staff:
                    staff[employee_id]['dayIndexesOFF'] = day_indexes_OFF
                    
              
            elif section == 'SECTION_SHIFT_ON_REQUESTS':
                employee_id, day, shift_id, weight = line.split(',')
                day = int(day)
                weight = int(weight)
                
                if 'shiftOnRequests' not in  staff[employee_id]:
                    staff[employee_id]['shiftOnRequests'] = {}
                

                staff[employee_id]['shiftOnRequests'].setdefault((day, shift_id), 0)
                staff[employee_id]['shiftOnRequests'][(day, shift_id)] += weight
                         
              
            elif section == 'SECTION_SHIFT_OFF_REQUESTS':
                employee_id, day, shift_id, weight = line.split(',')
                day = int(day)
                weight = int(weight)
                
                if 'shiftOffRequests' not in  staff[employee_id]:
                    staff[employee_id]['shiftOffRequests'] = {}

                staff[employee_id]['shiftOffRequests'].setdefault((day, shift_id), 0)
                staff[employee_id]['shiftOffRequests'][(day, shift_id)] += weight
                

            elif section == 'SECTION_COVER':
                day, shift_id, requirement_str, weight_under, weight_over = line.split(',')
                day = int(day)

                days[day][shift_id]['requirement'] = int(requirement_str)
                days[day][shift_id]['weightUnder'] = int(weight_under)
                days[day][shift_id]['weight_over'] = int(weight_over)
                
                    
                    
                
    
    #print(shifts) 
    #print(days)
    #print(staff)  
    #print(days)             
    return staff, days, shifts

staff, days, shifts = read_file('instances1_24//Instance1.txt')


import gurobipy as gp
from gurobipy import GRB

#modelo de otimização
m = gp.Model()

#variáveis de decisão
xid = m.addVars(staff, days, vtype=GRB.BINARY, name='xd')
kiw = m.addVars(staff,days, vtype=GRB.BINARY, name='kiw')

#Restrições

#Restrição MA1
for i in staff:
    for d in range(len(days) - staff[i]['maxConsecutiveShifts']):
        m.addConstr(
            gp.quicksum(xid[i,j] for j in range(d, d + staff[i]['maxConsecutiveShifts'])) <= staff[i]['maxConsecutiveShifts']
        )

#Restrição MA2
for i in staff:
    for c in range(staff[i]['minConsecutiveShifts'] - 1):
        for d in range(len(days) - (c + 1)):
            m.addConstr(
                xid[i,d] + c - 1 - gp.quicksum(xid[i,j] for j in range(len(days) + 1, d + c)) + xid[i,d+c+1]
            )

#Restrição MA3
# Verificando os dias disponíveis para iniciar a sequência de folga
for i in staff:
    min_days_off = staff[i]['minConsecutiveDaysOff']  # Acessando o número mínimo de dias de folga consecutivos
    for d in range(len(days) - min_days_off + 1):  # Ajustando o intervalo para garantir espaço para os dias de folga
        # Calculando a soma dos xd para os dias subsequentes
        sum_xd = gp.quicksum(xid[i, j] for j in range(d+1, d + min_days_off))
        # Adicionando a restrição: se xd[i, d] é 0 (dia de folga), então todos os próximos `min_days_off` dias também devem ser 0
        m.addConstr((1 - xid[i, d]) + sum_xd >= 0, name="MA3")








