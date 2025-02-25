import time
import boto3

# getting the processes data of the ec2 using ssm commands
def get_ec2_processes(instance_id, ssm):
    try:
        bash_script_base64 = "IyEvYmluL2Jhc2gKCnRvdWNoIC90bXAvcmVzdWx0cy50eHQKCmZvciBGT0xERVIgaW4gL3Byb2MvKjsgZG8KICAgICAgICBlY2hvICUhJSA+PiAvdG1wL3Jlc3VsdHMudHh0CgljYXQgJHtGT0xERVJ9L3N0YXR1cyB8IGdyZXAgTmFtZSA+PiAvdG1wL3Jlc3VsdHMudHh0CiAgICAgICAgY2F0ICR7Rk9MREVSfS9zdGF0dXMgfCBncmVwIC12IFRyYWNlciB8IGdyZXAgUGlkID4+IC90bXAvcmVzdWx0cy50eHQKCWVjaG8gIiBjbWRsaW5lOiIgPj4gL3RtcC9yZXN1bHRzLnR4dAogICAgICAgIGNhdCAke0ZPTERFUn0vY21kbGluZSA+PiAvdG1wL3Jlc3VsdHMudHh0CmRvbmUK"

        # -----------------------creating the script file---------------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [f"echo {bash_script_base64} | base64 -d > /tmp/script.sh"]})
        time.sleep(2)

        # ------------------ giving exe permission to the script--------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["chmod +x /tmp/script.sh"]})
        time.sleep(2)

        # --------------------- executing the script--------------------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["/tmp/script.sh"]})
        time.sleep(3)

        # ---------------------reading the results.txt------------------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["cat /tmp/results.txt"]})

        # fetching command id for the output
        command_id = response["Command"]["CommandId"]

        # must wait for the command to finish 
        time.sleep(2)

        # fetching command output
        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)["StandardOutputContent"]

        # ---------------------removing the results.txt------------------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["rm /tmp/results.txt"]})

        # ---------------------removing the script------------------------------
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["sudo rm /tmp/script.sh"]}) 

        analayzed_output = analayze_processes(output, instance_id) 

        return analayzed_output
    except Exception as e:
        print(str(e))

# extracting the process parameters into a dictionary      
def analayze_processes(output, instance_id):
    try:
        processes = []
        new_output = output.replace('\t',"").replace("Pid", " Pid").replace("P Pid"," PPid").replace("\n", "").replace('\x00', "")
        # seperating outout into array of processes
        p_list = new_output.split("%!%") 
        p_list.pop(0)
        
        for p in p_list:
            if len(p.split(" ")) <= 2:
                break
            params = p.split(" ")
            for word in params:
                if word == " ":
                    params.remove(word)
                    
            name = params[0][5:]
            pid = params[1][4:]
            ppid = params[2][5:]
            cmdline = " ".join(params[3:]).replace("cmdline:","")
            
            if cmdline == "":
                cmdline = "daemon"
            
            process = {
                "instance_id":instance_id,
                "name": name,
                "process_id":pid,
                "parent_p_id":ppid,
                "cmdline":cmdline
            }
            processes.append(process)
        return processes
        
    except Exception as e:
        print(str(e))

def lambda_handler(event, context):
    try:
        instance_id = event.get("instance_id")
        ssm_client = boto3.client("ssm")
        results = get_ec2_processes(instance_id, ssm_client)
    except Exception as e:
        print(str(e))
        exit()

    return {"statusCode": 200, "output": results}
