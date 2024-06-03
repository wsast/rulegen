import os
import sys
import openai
import threading

if len(sys.argv) != 3:
    print("Usage: rulegen.py <type> <input>")
    sys.exit(0)

rule_type = sys.argv[1].strip()

if rule_type not in ["source", "sink"]:
    print("Parameter 'type' must be 'source' or 'sink'")
    sys.exit(0)

if not os.path.exists(rule_type):
    os.mkdir(rule_type)

if not os.path.exists(sys.argv[2]):
    print("Parameter 'input' must be a file containing class names")
    sys.exit(0)

with open(sys.argv[2], "r") as f:
    input_classes = f.readlines()

thread_count = 6
threads = []

while input_classes:
    def threadproc(class_name):
        client = openai.OpenAI(api_key = "<api key from OpenAI>")

        with open(r"prompt-function-%s-1.txt" % rule_type, "r", encoding="utf-8") as f:
            system_prompt_1 = f.read()

        with open(r"prompt-function-%s-2.txt" % rule_type, "r", encoding="utf-8") as f:
            user_prompt = f.read()

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt_1.replace("{class-name}", class_name)
                },
                {
                    "role": "user",
                    "content": user_prompt.replace("{class-name}", class_name)
                }
            ]
        )

        result = completion.choices[0].message.content

        print("GPT produced for class '%s':\n\n%s" % (class_name, result))

        index_start = result.find("<function")
        index_end = result.rfind("</function>")

        if index_start < 0 or index_end < 0 or index_end < index_start:
            print("GPT failed to generate any valid rules for class '%s'" % class_name)
            return
    
        with open(rule_type + "\\" + class_name + ".xml", "w") as f:
            f.write(result[index_start:index_end + 11])
    
    t = threading.Thread(target=threadproc, args=(input_classes.pop().strip(),))
    t.start()
    
    threads.append(t)
    
    if not input_classes or (len(threads) % thread_count) == 0:
        for t in threads: t.join()
        threads = []