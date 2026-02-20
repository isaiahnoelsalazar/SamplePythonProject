from flask import Flask, request, render_template, jsonify
import pymssql
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello'


@app.route('/test')
def test():
    return render_template("test.html")


@app.route('/test-json')
def test_json():
    return jsonify({"response_data": "Test JSON"})


@app.route('/about')
def about():
    return sys.version


@app.route("/mssql_query")
def python_mssql_query():
    try:
        print("test0")
        server = request.args.get("server")
        database = request.args.get("database")
        username = request.args.get("username")
        password = request.args.get("password")
        query = request.args.get("query")
        print("test1")
        print(server, database, username, password)
        connection = pymssql.connect(server, username, password, database)
        print("test2")

        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        data = ""

        print("test3")

        for row in rows:
            data += str(row) + ","


        data = {"response_data": data.strip()[:-1]}


        connection.close()

        return jsonify(data)
    except Exception as e:
        return jsonify({"response_data": str(e)})


@app.route("/mssql_execute")
def python_mssql_execute():
    try:
        server = request.args.get("server")
        database = request.args.get("database")
        username = request.args.get("username")
        password = request.args.get("password")
        execute = request.args.get("execute")

        connection = pymssql.connect(server, username, password, database)

        cursor = connection.cursor()
        cursor.execute(execute)
        connection.commit()
        connection.close()

        return jsonify({"response_data": "Command completed."})
    except:
        return jsonify({"response_data": "Connection broken. Please check your parameters again."})

if __name__ == '__main__':
    app.run(debug=True)