import louis

# 텍스트 -> 점자 변환
text = "abc"
result = louis.translateString(["en-us-g1.ctb"], text)
print(result)  # 출력: "⠁⠃⠉" (점자 a, b, c)
