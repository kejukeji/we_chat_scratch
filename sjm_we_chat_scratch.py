# coding: utf-8

from scratch import app

import sys
reload(sys)
sys.setdefaultencoding('UTF-8')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7079, debug=True)