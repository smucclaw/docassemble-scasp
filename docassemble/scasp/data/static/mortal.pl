#pred mortal(X) :: '@(X) is mortal'.
#pred human(X) :: '@(X) is human'.

mortal(X) :- human(X).

human(socrates).

?- mortal(X).