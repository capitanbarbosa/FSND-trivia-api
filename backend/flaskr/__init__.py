import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request,selection):
  page = request.args.get('page',1, type=int)
  start = (page-1)* QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE
  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/api/*": {"origins":"*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
      response.headers.add('Access-Control-Allow-Methods','GET, POST, PATCH, DELETE, OPTIONS')
      return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    categories_list = {}
    for category in categories:
      categories_list[category.id] = category.type

    if len(categories_list) == 0:
            abort(404)

    return jsonify({
      'success': True,
      'categories': categories_list
    })



  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    question_list = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, question_list)

    categories_list = Category.query.all()
    categories = []

    for category in categories_list:
      categories[category.id] = category.type

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(question_list),
      'current_category': None,
      'categories': categories
    })



  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.filter_by(id=question_id).one_or_none()
    if (question is None):
      abort(404)

    question.delete()

    return jsonify({
      'success': True,
      'deleted': question_id
    })


  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def post_question():
    data = request.get_json()

    if not ('category' in data and 'question' in data and 'difficulty' in data and 'answer' in data):
      abort(422)
    
    question = data.get('question')
    answerText = data.get('answer')
    difficulty = data.get('difficulty')
    category = data.get('category')

    try:
      question = Question(category=category, 
                          question=question, 
                          difficulty=difficulty, 
                          answer=answerText)
      question.insert()
      return jsonify({
        'success': True,
        'questionPosted': question.id
      })
    except:
      abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions', methods=['POST'])
  def search_question():
    data = request.get_json()
    search = data.get('searchTerm', None)

    if search:
      results = Question.query.filter(Question.question.ilike(f'%{search}%')).all()

      return jsonify({
        'success': True,
        'questions': [question.format() for question in results],
      })
    abort(404) 




  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_question_by_category(category_id):
    try:
      questions_list = Question.query.filter(Question.category == str(category_id)).all()

      return jsonify({
        'success': True,
        'questions': [question.format() for question in questions_list],
        'total_questions': len(questions_list),
        'current_category': category_id
      })
    except:
      abort(404)
      

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_quizzes():
    try:
      data = request.get_json()

      if not ('quiz_category' in data and 'previous_questions' in data):
        abort(422)

      category = data.get('quiz_category')
      previous_questions= data.get('previous_questions')

      #the user ticks 'All' .
      if category['type'] == 'click':
          available_questions_list = Question.query.filter(Question.id.notin_((previous_questions))).all()
      else:
          available_questions_list = Question.query.filter_by(category=category['id']).filter(Question.id.notin_((previous_questions))).all()

      new_question = available_questions_list[random.randrange(0, len(available_questions_list))].format() if len(available_questions_list) > 0 else None

      return jsonify({
          'success': True,
          'question': new_question
      })
    except:
        abort(422)


  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def badRequest(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': "Malformed request"
    }), 400

  @app.errorhandler(404)
  def notFound(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "Page not Found"
    }), 404

  @app.errorhandler(422)
  def unprocessableEntity(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "Unprocessable entity"
    }), 422

  @app.errorhandler(500)
  def internalError(error):
    return jsonify({
      'success': False,
      'error': 500,
      'message': "Internal Server Error"
    }), 500


  
  return app

    