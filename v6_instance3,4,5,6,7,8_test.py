#from gurobipy import Model, GRB


# Definindo as estruturas de dados como dicionários ou listas
#days = {}
#staff = {}

# Função para ler o arquivo
def read_file(filename):
    staff = {}
    days = {}
    shifts = [] #mudar pra dicionário
    

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

staff, days, shifts = read_file('ModeloPythonLocal//instances1_24//Instance9.txt')



import gurobipy as gp
from gurobipy import GRB

#modelo de otimização
m = gp.Model()
#m.update()
#variáveis de decisão
xidt = m.addVars(staff, days, shifts, vtype=GRB.BINARY, name='xidt')
kiw = m.addVars(staff, days, vtype=GRB.BINARY, name='kiw')
ydt = m.addVars(days, shifts, vtype=GRB.INTEGER, name='ydt')
zdt = m.addVars(days, shifts, vtype=GRB.INTEGER, name='zdt')

# Penalidades
vidt = m.addVars(staff, days, shifts, vtype=GRB.CONTINUOUS, name="vidt")
#print(xidt)

#print(staff)

#Função objetiva min
objective = gp.quicksum(
    vidt[i, d, t] for i in staff for d in days for t in shifts  
) + gp.quicksum(
    days[d][t]['weightUnder'] * ydt[d, t]  for d in days for t in shifts 
) + gp.quicksum(
    days[d][t]['weight_over'] * zdt[d, t]  for d in days for t in shifts
)

m.setObjective(objective, GRB.MINIMIZE)
#print(objective)
#print(shifts)
#print(days)
#print(staff)
#print(shifts)

#Restrições fortes:

#Restrição HC1
for i in staff:
    for d in days:
        m.addConstr(gp.quicksum(xidt[i, d, t] for t in shifts) <= 1, name="HC1")


#Restrição HC2
for i in staff:
    for d in range(len(days) - 1):
        for t in shifts:
            cannot_follow_shifts = days[d+1][t].get('cannotFollow', [])
            if cannot_follow_shifts:
                for t_next in cannot_follow_shifts:
                    m.addConstr(xidt[i, d, t] + xidt[i, d+1, t_next] <= 1, name="HC2")

#Restrição HC3
for i in staff:
    for t in shifts:
        m.addConstr(
            gp.quicksum(xidt[i, d, t] for d in days) <= staff[i]['shifts'][t]['maxShifts'], name="HC3"
        )

#Restrição HC4 e HC5
for i in staff:
       total_hours = gp.quicksum(days[d][t]['lengthInMins'] * xidt[i, d, t] for d in days for t in shifts)
       m.addConstr(total_hours >= staff[i]['minTotalMinutes'], name="HC4")
       m.addConstr(total_hours <= staff[i]['maxTotalMinutes'], name="HC5")


#Restrição HC6
for i in staff:
    for d in range(len(days) - staff[i]['maxConsecutiveShifts']):
        m.addConstr(
            gp.quicksum(xidt[i, j, t] for j in range(d, d + staff[i]['maxConsecutiveShifts'] + 1) for t in shifts) <= staff[i]['maxConsecutiveShifts'], name="HC6"
    )
        
#Restrição HC7
for i in staff:
    for c in range(1, staff[i]['minConsecutiveShifts']):
        for d in range(len(days) - (c + 1) ):    
            sum1 = gp.quicksum(xidt[i, d, t] for t in shifts) + c - 1
            sum2 = gp.quicksum(xidt[i, j, t] for j in range(d+1, d+c+1) for t in shifts)
            sum3 = gp.quicksum(xidt[i, d+c+1, t] for t in shifts)
            m.addConstr((sum1 - sum2 + sum3) >=  0)

#Restrição HC8
for i in staff:
    for b in range(1, staff[i]['minConsecutiveDaysOff']):
        for d in range(len(days) - (b+1)):
            sum1 = gp.quicksum(xidt[i, d, t] for t in shifts)
            sum2 = gp.quicksum(xidt[i, j, t] for j in range(d+1, d+b+1) for t in shifts)
            sum3 = gp.quicksum(xidt[i, d+b+1, t] for t in shifts)
            
            m.addConstr(
                1 - sum1 + sum2 - sum3 >= 0, name='HC8'
            )

#Restrição HC9
for i in staff:
    for w in range(1, len(days)//7 + 1):
        worked_weekend_days = gp.quicksum(xidt[i, 7*w - 2, t] + xidt[i, 7*w - 1, t] for t in shifts)
        m.addConstr((worked_weekend_days >= kiw[i, w]), name='HC9_1')
        m.addConstr((worked_weekend_days <= 2*kiw[i, w]), name='HC9_2')
      

#Restrição HC9_3
for i in staff:
    m.addConstr(
        gp.quicksum(kiw[i, w] for w in range(1, len(days)//7 + 1)) <= staff[i]['maxWeekends'], name='HC9_3'
    )
        
#Restrição HC10
for i in staff:
    for n in staff[i]['dayIndexesOFF']:
        for t in shifts:
            m.addConstr(
                xidt[i, n, t] == 0, name='HC10'
            )


#Restrição SC1
for i in staff:
    for d in days:
        for t in shifts:
            if 'shiftOnRequests' in staff[i]:
                shift_on_req = staff[i]['shiftOnRequests'].get((d, t), 0)  # 0 se não existir
            else:
                shift_on_req = 0
            if 'shiftOffRequests' in staff[i]:
                shift_off_req = staff[i]['shiftOffRequests'].get((d, t), 0)  # 0 se não existir
            else:
                shift_off_req = 0

            
            m.addConstr(
                shift_on_req * (1 - xidt[i, d, t]) + shift_off_req * xidt[i, d, t] == vidt[i, d, t], 
                name='SC1'
            )

#Restrição SC2
for d in days:
    for t in shifts:
        m.addConstr(
            gp.quicksum(xidt[i, d, t] for i in staff) - zdt[d, t] + ydt[d, t]  == days[d][t]['requirement'], name='SC2'
        )


#m.update()

#m.setParam("TimeLimit", 60)

#m.optimize()




#m.update()
#print(m)
#print(days)
#print(shifts)
#print(staff)





    




