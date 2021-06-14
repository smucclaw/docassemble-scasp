#pred mortal(X) :: '@(X) can die'.
#pred human(X) :: '@(X) is human'.
#pred alive(X) :: '@(X) is alive'.

mortal(X) :-
	human(X),
	alive(X).


human(socrates).
alive(socrates).

?- mortal(X).
