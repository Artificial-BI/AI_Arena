 
user_id = 1234
once = {}
 
 
print('>>',once.get(user_id))
 
if not once.get(user_id):
    once[user_id] = True
    print('<<<-1',once.get(user_id))
     
     
if once.get(user_id):
    once[user_id] = True
    print('<<<-2',once.get(user_id))     