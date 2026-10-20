FROM busybox:1.37.0 


WORKDIR /app 


COPY --from=svroman0502/kbtu-devops-bomb:1.0.0 /hello.txt /hello.txt

CMD ["cat","/hello.txt"]