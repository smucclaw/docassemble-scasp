winner_of_game(Player,Game) :-
  player(Player),
  player(OtherPlayer),
  Player \= OtherPlayer,
  game(Game),
  player_in_game(Player,Game),
  player_in_game(OtherPlayer,Game),
  player_threw_sign(Player,Sign),
  player_threw_sign(OtherPlayer,OtherSign),
  sign_beats_sign(Sign,OtherSign).

%player(1).
%player(2).

%game(testgame).

#abducible game(X).
#abducible player(X).
#abducible player(1).

sign_beats_sign(rock,scissors).
sign_beats_sign(scissors,paper).
sign_beats_sign(paper,scissors).

#abducible player_threw_sign(A,B).
#abducible player_in_game(A,B).

%winner_of_game(jason,game).

?- winner_of_game(P,G).