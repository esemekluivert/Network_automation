from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from .models import Device, Log
from datetime import datetime
import paramiko
import time

# Create your views here.
def home(request):
    all_device= Device.objects.all()
    mikrotik_device= Device.objects.filter(vendor='mikrotik')
    cisco_device=Device.objects.filter(vendor='cisco')
    all_logs=Log.objects.all().order_by('-id')[:10]
    context = {

        'all_device': len(all_device),
        'mikrotik_device': len(mikrotik_device),
        'cisco_device':len(cisco_device),
        'all_logs': all_logs
    }

    return render(request, "home.html", context)

def devices(request):
    all_device = Device.objects.all()
    context = {
        'all_device': all_device
    }
    return render(request, "devices.html", context)

def configure(request):
    if request.method == "POST":
        select_device_id = request.POST.getlist('device')
        mikrotik_command = request.POST['mikrotik_command'].splitline()
        cisco_command = request.POST['cisco_command'].splitline()
        for x in select_device_id:
            try:
                dev= get_object_or_404(Device, pk=x)
                ssh_client= paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=dev.ip_address, username=dev.username, password= dev.password)
                if dev.vendor.lower() == "cisco":
                    conn=ssh_client.invoke_shell()
                    conn.send("conf t\n")
                    for cmd in cisco_command:
                        conn.send(cmd +"\n")
                        time.sleep(1)
                else: 
                    for cmd in mikrotik_command:
                        ssh_client.exec_command(cmd)
                log= Log(target=dev.ip_address, action='configure', status="Error", time=datetime.now(), message=e)
                log.save()
            except Exception as e:
                log= Log(target=dev.ip_address, action='configure', status="Error", time=datetime.now(), message=e)
                log.save()
        return redirect('home')
    else:
        all_device= Device.objects.all()
        context = {
        'all_device': all_device,
        'mode': 'configure'
    }
        return render(request, "config.html", context)

def verify_config(request):
    if request.method == "POST":
        select_device_id= request.POST.getlist('device')
        cisco_command= request.POST['cisco'].splitline()
        mikrotik_command= request.POST['mikrotik'].splitline()
        for x in select_device_id:
            try:
                result = []
                dev= get_object_or_404(Device, pk=x)
                ssh_client= paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=dev.ip_address, username=dev.username, password=dev.password)

                if  dev.vendor.lower() == 'mikrotik':
                    for cmd in mikrotik_command:
                        stdin,stdout,stderr = ssh_client.exec_command(cmd)
                        result.append(f"Result of {dev.ip_address}")
                        result.append(stdout.read().decode())
                else:
                    conn= ssh_client.invoke_shell
                    conn.send('terminal length 0\n')
                    for cmd in cisco_command:
                        result.append(f"Result of {dev.ip_address}")
                        conn.send(cmd + "\n")
                        time.sleep(1)
                        output = conn.recv(65535).decode()
                        result.append(output)
                log= Log(target=dev.ip_address, action='verify_config', status="Succes", time=datetime.now(), message="No Error")
                log.save()
            except Exception as e:
                log= Log(target=dev.ip_address, action='verify_config', status="Error", time=datetime.now(), message=e)
                log.save()

            
        result = '\n'.join(result)
        return render(request, "verify_config.html", {'result': result})
    else:	
        all_device = Device.objects.all()
        context = {

			'all_device': all_device,
             'mode': 'verify_config'
        }
        return render(request, 'configure.html', context)

def logs(request):
    all_logs= Log.objects.all()
    context = {

        'all_logs': all_logs
    }

    return render(request, "log.html", context)


