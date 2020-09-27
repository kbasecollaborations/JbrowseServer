Dyanmic server to support byte ranges for variation workflows


To test 
</br>

(copy .env.example to .env and update token information in .env)
</br>
<code>cp .env.example  .env</code>

</br>
<code>docker-compose up</code>

</br>
Run tests with (currently working for  appdev)

</br>
<code>docker-compose run web test </code>
</br>

<p>
Once the service is running, it can also be tested in the following way.
The following can be adapted for any environment by changing url and 


http://0.0.0.0:5000/jbrowse/x/y/z/index.html

eg for appdev settings in .env you can look at 
http://0.0.0.0:5000/jbrowse/47506/18/1/index.html 

</p>


