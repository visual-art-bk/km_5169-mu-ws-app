def get_style_target_site_btn(active: bool = False):
    if active == True:
        return """
        QPushButton {
                    background-color: green;  /* 배경색 초록색 */
                    color: white;             /* 글자색 흰색 */
                }
        """
    else:
        return """
            QPushButton {
                background-color: white;   /* 배경색 회색 */
                color: black;             /* 글자색 검정색 */
            }
        """
