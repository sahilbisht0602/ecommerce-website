from django.shortcuts import render
from django.http import HttpResponse
from .models import Product,Contact,Orders,orderupdate
from math import ceil
from django .views .decorators .csrf import csrf_exempt
from payTm import Checksum
import json
MERCHANT_key='8r1vFZAkuPviSHvG'
# Create your views here.
def index(request):
    allProds = []
    catprods=Product.objects.values('category')
    print(catprods)
    #getting unique value in set of categories
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod=Product.objects.filter(category=cat)
        print(prod)
        n=len(prod)
        #no. of slides for first query set
        nslides=n//4+ceil((n/4)-(n//4))
        allProds.append([prod,range(1,nslides)])

    params={'allProds': allProds}
    return render(request,'shop/index.html',params)
def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.Product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    prodtemp=Product.objects.all()
    prod = [item for item in prodtemp if searchMatch(query, item)]
    print(prod)
    n = len(prod)
    nSlides = n // 4 + ceil((n / 4) - (n // 4))
    if len(prod) != 0:
        allProds.append([prod, range(1, nSlides)])
    params = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)
def about(request):
    return render(request,'shop/about.html')
def contact(request):
    thank=False
    if request.method=="POST":
        name=request.POST.get('name'," ")
        email=request.POST.get('email'," ")
        phone=request.POST.get('phone'," ")
        desc=request.POST.get('desc'," ")
        contact=Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        thank=True
    return render(request,'shop/contact.html',{'thank':thank})
def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = orderupdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps(updates, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')

    return render(request, 'shop/tracker.html')

def product(request,myid):
    product = Product.objects.filter(id=myid)
    print(product)
    return render(request,'shop/prodview.html',{'product':product[0]})
def checkout(request):
    if request.method=="POST":
        item_json=request.POST.get('item_json'," ")
        name=request.POST.get('name'," ")
        amount=request.POST.get('amount'," ")
        email=request.POST.get('email'," ")
        phone=request.POST.get('phone'," ")
        city=request.POST.get('city'," ")
        zip_code=request.POST.get('zip_code'," ")
        address=request.POST.get('address1'," ")+" "+request.POST.get('address2'," ")
        state=request.POST.get('state'," ")
        order=Orders(name=name,amount=amount,email=email,phone=phone,city=city,zip_code=zip_code,address=address,state=state,item_json=item_json)
        order.save()
        update=orderupdate(order_id=order.order_id,update_desc="Your order has been placed")
        update.save()
        thank=True
        id=order.order_id
        #return render(request,'shop/checkout.html',{'thank':thank,'id':id})
        #request paytm to transfer the amount to your account after payment by user
        param_dict={
            'MID': 'DshAXY53546894347172',
            'ORDER_ID':str(order.order_id),
            'TXN_AMOUNT':str(amount),
            'CUST_ID':email,
            'INDUSTRY_TYPE_ID':'Retail',
            'WEBSITE':'WEBSTAGING',
            'CHANNEL_ID':'WEB',
	        'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
        }
        param_dict['CHECKSUMHASH']=Checksum.generate_checksum(param_dict,MERCHANT_key)
        return render(request,'shop/paytm.html',{'param_dict':param_dict})
    return render(request,'shop/checkout.html')
@csrf_exempt #we will pass csrf for this function
def handlerequest(request):
    #paytm will send you post request here
    form=request.POST
    resposepaytm_dict={}
    for i in form:
        resposepaytm_dict[i]=form[i]
        if i=='CHECKSUMHASH':
            checksum=form[i]

    verify=Checksum.verify_checksum(resposepaytm_dict,MERCHANT_key,checksum)
    if verify:
        if resposepaytm_dict['RESPCODE']=='01':
            print("THANKS FOR SHOP WITH US YOUR ORDER IS SUCESSFULLY PLACED")
        else:
            print("failure during payment"+resposepaytm_dict['RESPMSG'])

    return render(request,'shop/paymentstatus.html',{'response':resposepaytm_dict})