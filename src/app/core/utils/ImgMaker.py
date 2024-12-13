import os
import requests


def save_imgs(image_dict: dict):
    """
    이미지 딕셔너리 데이터를 받아 각 카테고리별로 디렉토리를 생성하고 이미지를 저장합니다.

    Args:
        image_dict (dict): {'카테고리': {'출원번호': '이미지 URL'}} 형태의 딕셔너리

    저장 구조:
        - 상표권출원등록사진/
            ├── 컴포트/
            │   ├── 3237434.jpg
            │   ├── 32343233.jpg
            ├── 무신사/
            │   ├── 50940345.jpg
    """
    # 최상위 디렉토리 생성
    base_dir = "상표권출원등록사진"
    os.makedirs(base_dir, exist_ok=True)

    # 카테고리별 처리
    for category, application_data in image_dict.items():
        # 카테고리별 디렉토리 생성
        category_dir = os.path.join(base_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        for application_number, image_url in application_data.items():
            try:
                # 이미지 다운로드
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    # 파일 저장 경로 설정
                    file_name = f"{application_number}.jpg"
                    file_path = os.path.join(category_dir, file_name)

                    # 이미지 저장
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)

                    print(f"저장 완료: {file_path}")
                else:
                    print(
                        f"이미지 다운로드 실패: {image_url} (상태 코드: {response.status_code})"
                    )
            except Exception as e:
                print(f"오류 발생: {e}, URL: {image_url}")

    print("모든 이미지 저장이 완료되었습니다.")
