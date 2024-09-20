from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dbutil import create_db_connection
import logging
from datetime import datetime

# 블루프린트 정의
student_clean_bp = Blueprint('student_clean', __name__)

# 허용된 파일 확장자 설정
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 사진 업로드 엔드포인트
@student_clean_bp.route('/student/upload_clean_photos', methods=['POST'])
def upload_clean_photos():
    # 요청으로부터 학생 학번 및 방 번호, 자리 번호 가져오기
    student_number = request.form.get('student_number')
    room_number = request.form.get('room_number')
    seat_number = request.form.get('seat_number')

    if not student_number or not room_number or not seat_number:
        return jsonify({'error': 'Student number, room number, and seat number are required'}), 400

    # 파일 체크: 사진은 최소 1장, 최대 4장이어야 함
    files = request.files.getlist('photos')
    if len(files) < 1 or len(files) > 4:
        return jsonify({'error': 'You must upload at least 1 and at most 4 photos'}), 400

    # 업로드할 파일의 유효성 검사
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'All files must be in the allowed formats (png, jpg, jpeg, gif)'}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # 파일 바이너리 처리 및 저장
        photo_blobs = []
        for file in files:
            photo_blob = file.read()  # 파일을 바이너리 형식으로 읽음
            photo_blobs.append(photo_blob)

        # WARN의 기본값을 0으로 설정
        warn_default = 0

        # BLOB 컬럼에 사진을 저장하기 위한 쿼리
        update_query = """
            UPDATE CLEAN 
            SET PIC1 = %s, PIC2 = %s, PIC3 = %s, PIC4 = %s, WARN = %s 
            WHERE CROOM = %s AND CSEATUM = %s
        """
        
        # 4개 미만의 사진이 업로드되면 남은 PIC 칼럼은 NULL로 설정
        while len(photo_blobs) < 4:
            photo_blobs.append(None)

        cursor.execute(update_query, (*photo_blobs, warn_default, room_number, seat_number))

        connection.commit()
        return jsonify({'message': 'Photos uploaded successfully'}), 200

    except Exception as e:
        logging.error(f"Error during photo upload: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
