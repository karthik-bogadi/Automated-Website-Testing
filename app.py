from flask import Flask, render_template, request, jsonify
from agents.langGraph_agent import graph

app = Flask(__name__)


# Home page
@app.route('/')
def home():
    return render_template('index.html')


# LangGraph API
@app.route("/langgraph", methods=["POST"])
def langgraph_agent():
    instruction = request.json.get("instruction")

    result = graph.invoke({"input": instruction})

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)