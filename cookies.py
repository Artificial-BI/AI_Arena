

from flask import request, make_response

class Cookies:
    
    def set_cookie(self, response, key, value, max_age=3600):
        response.set_cookie(key, value, max_age=max_age)
        return response

    def get_cookie(self, key):
        return request.cookies.get(key)

    def check_cookie(self, key):
        return key in request.cookies
    
    def set_cookie_for_user(self, response, user_id, key, value, max_age=3600):
        cookie_key = f"user_{user_id}_{key}"
        response.set_cookie(cookie_key, value, max_age=max_age)
        return response

    def get_cookie_for_user(self, user_id, key):
        cookie_key = f"user_{user_id}_{key}"
        return request.cookies.get(cookie_key)

    def increment_cookie_for_user(self, response, user_id, key, max_age=3600):
        cookie_key = f"user_{user_id}_{key}"
        current_value = request.cookies.get(cookie_key, '0')
        try:
            new_value = str(int(current_value) + 1)
        except ValueError:
            new_value = '1'
        response.set_cookie(cookie_key, new_value, max_age=max_age)
        return response
    
    def is_odd(self, user_id):
        step_read_value = self.get_cookie_for_user(user_id, 'step_read')
        #print(f'step_read_value {user_id}:',step_read_value)
        if step_read_value is None:
            step_read_value = '0'
        try:
            number = int(step_read_value)
        except ValueError:
            number = 0
        return number % 2 != 0
