import google.generativeai as genai

genai.configure(api_key="AIzaSyBqUwcbOBNGXpb0X7Y1DyNzVEvGqRtpXH4")

models = genai.list_models()

for m in models:
    print(m.name)
