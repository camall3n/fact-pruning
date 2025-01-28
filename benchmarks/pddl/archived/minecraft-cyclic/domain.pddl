(define (domain minecraft-cyclic)
    (:requirements :strips)

    (:types
        agent int - object
    )

    (:predicates
        ; ---------- inventory ----------
        (hungry ?ag - agent)
        (tribe-has-food - agent)
        (has-logs ?ag - agent ?n - int)
        (has-sticks ?ag - agent ?n - int)
        (has-planks ?ag - agent)
        (has-stone ?ag - agent)
        (has-iron ?ag - agent ?n - int)
        (has-wool ?ag - agent ?n - int)
        (has-string ?ag - agent)
        ; ---------- equipment ----------
        (has-basket ?ag)
        (has-wood-pickaxe ?ag)
        (has-stone-pickaxe ?ag)
        (has-stone-axe ?ag)
        (has-shears ?ag)
        (has-fork ?ag)
        (has-bow ?ag)
        ; ---------- misc ----------
        (tribe-has-food)
        (has-bed ?ag)
        (are-seq ?x1 - int ?x2 - int) ;; true if x1 + 1 = x2 (i.e. they are sequential)
    )
    ; ---------- resources ----------

    (:functions
        (total-cost) - number
    )

    (:action chop-tree
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-logs ?ag ?n_start)
            (are-seq ?n_start ?n_end)
        )
        :effect (and
            (not (has-logs ?ag ?n_start))
            (has-logs ?ag ?n_end)
        )
    )

    (:action destroy-bush
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-sticks ?ag ?n_start)
            (are-seq ?n_start ?n_end)
        )
        :effect (and
            (not (has-sticks ?ag ?n_start))
            (has-sticks ?ag ?n_end)
        )
    )

    (:action mine-stone
        :parameters (?ag - agent)
        :precondition (or
            (has-wood-pickaxe ?ag)
            (has-stone-pickaxe ?ag)
        )
        :effect (and (has-stone ?ag))
    )

    (:action mine-iron
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-stone-pickaxe ?ag)
            (has-iron ?ag ?n_start)
            (are-seq ?n_start ?n_end)
        )
        :effect (and
            (not (has-iron ?ag ?n_start))
            (has-iron ?ag ?n_end)
        )
    )

    (:action shear-sheep
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-shears ?ag)
            (has-wool ?ag ?n_start)
            (are-seq ?n_start ?n_end)
        )
        :effect (and
            (not (has-wool ?ag ?n_start))
            (has-wool ?ag ?n_end)
        )
    )

    ; ---------- crafting ----------

    (:action craft-basket
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-sticks ?ag ?n_start)
            ; n_sticks >= 3
            (exists
                (?n_minus_one - int)
                (exists
                    (?n_minus_two - int)
                    (and
                        (are-seq ?n_end ?n_minus_two)
                        (are-seq ?n_minus_two ?n_minus_one)
                        (are-seq ?n_minus_one ?n_start)
                    )
                )
            )
            (not (has-basket ?ag))
        )
        :effect (and
            (not (has-sticks ?ag ?n_start))
            (has-sticks ?ag ?n_end)
            (has-basket ?ag)
        )
    )

    (:action craft-planks
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-logs ?ag ?n_start)
            ; n_logs >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
        )
        :effect (and
            (not (has-logs ?ag ?n_start))
            (has-logs ?ag ?n_end)
            (has-planks ?ag)
        )
    )

    (:action craft-wood-pickaxe
        :parameters (?ag1 - agent ?n_start - int ?n_end - int ?ag2 - agent ?ag3 - agent)
        :precondition (and
            (has-sticks ?ag1 ?n_start)
            ; n_sticks >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
            (has-planks ?ag2)
            (not (has-wood-pickaxe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1 ?n_start))
            (has-sticks ?ag1 ?n_end)
            (not (has-planks ?ag2))
            (has-wood-pickaxe ?ag3)
        )
    )

    (:action craft-stone-pickaxe
        :parameters (?ag1 - agent ?n_start - int ?n_end - int ?ag2 - agent ?ag3 - agent)
        :precondition (and
            (has-sticks ?ag1 ?n_start)
            ; n_sticks >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
            (has-stone ?ag2)
            (not (has-stone-pickaxe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1 ?n_start))
            (has-sticks ?ag1 ?n_end)
            (not (has-stone ?ag2))
            (has-stone-pickaxe ?ag3)
        )
    )

    (:action craft-stone-axe
        :parameters (?ag1 - agent ?n_start - int ?n_end - int ?ag2 - agent ?ag3 - agent)
        :precondition (and
            (has-sticks ?ag1 ?n_start)
            ; n_sticks >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
            (has-stone ?ag2)
            (not (has-stone-axe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1 ?n_start))
            (has-sticks ?ag1 ?n_end)
            (not (has-stone ?ag2))
            (has-stone-axe ?ag3)
        )
    )

    (:action craft-shears
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-iron ?ag ?n_start)
            ; n_iron >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
            (not (has-shears ?ag))
        )
        :effect (and
            (not (has-iron ?ag ?n_start))
            (has-iron ?ag ?n_end)
            (has-shears ?ag)
        )
    )

    (:action craft-fork
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-iron ?ag ?n_start)
            ; n_iron >= 1
            (are-seq ?n_end ?n_start)
            (not (has-fork ?ag))
        )
        :effect (and
            (not (has-iron ?ag ?n_start))
            (has-iron ?ag ?n_end)
            (has-fork ?ag)
        )
    )

    (:action craft-string
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-wool ?ag ?n_start)
            ; n_wool >= 1
            (are-seq ?n_end ?n_start)
            (not (has-string ?ag))
        )
        :effect (and
            (not (has-wool ?ag ?n_start))
            (has-wool ?ag ?n_end)
            (has-string ?ag)
        )
    )

    (:action craft-bow
        :parameters (?ag1 - agent ?n_start - int ?n_end - int ?ag2 - agent ?ag3 - agent)
        :precondition (and
            (has-sticks ?ag1 ?n_start)
            ; n_sticks >= 1
            (are-seq ?n_end ?n_start)
            (has-string ?ag2)
            (not (has-bow ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1 ?n_start))
            (has-sticks ?ag1 ?n_end)
            (not (has-string ?ag2))
            (has-bow ?ag3)
        )
    )

    (:action craft-bed
        :parameters (?ag - agent ?n_start - int ?n_end - int)
        :precondition (and
            (has-wool ?ag ?n_start)
            ; n_wool >= 2
            (exists
                (?n_minus_one - int)
                (and
                    (are-seq ?n_end ?n_minus_one)
                    (are-seq ?n_minus_one ?n_start)
                )
            )
            (has-planks ?ag)
            (not (has-bed ?ag))
        )
        :effect (and
            (not (has-wool ?ag ?n_start))
            (has-wool ?ag ?n_end)
            (not (has-planks ?ag))
            (has-bed ?ag)
        )
    )

    ; ---------- food ----------

    (:action hunt-with-fists
        :parameters (?ag - agent)
        :precondition (and
            (not (hungry ?ag))
        )
        :effect (and
            (tribe-has-food)
            (hungry ?ag)
            (increase (total-cost) 50)
        )
    )

    (:action hunt-with-axe
        :parameters (?ag - agent)
        :precondition (and
            (has-stone-axe ?ag)
            (not (hungry ?ag))
        )
        :effect (and
            (tribe-has-food)
            (hungry ?ag)
            (increase (total-cost) 50)
        )
    )

    (:action hunt-with-bow
        :parameters (?ag - agent)
        :precondition (and
            (has-bow ?ag)
            (not (hungry ?ag))
        )
        :effect (and
            (tribe-has-food)
            (hungry ?ag)
            (increase (total-cost) 50)
        )
    )

    (:action gather
        :parameters (?ag - agent)
        :precondition (and
            (hungry ?ag)
        )
        :effect (and
            (tribe-has-food)
            (increase (total-cost) 50)
        )
    )

    (:action eat-snack
        :parameters (?ag - agent)
        :precondition (and
            (tribe-has-food)
            (hungry ?ag)
        )
        :effect (and
            (not (tribe-has-food))
            (not (hungry ?ag))
        )
    )

    (:action eat-meal
        :parameters (?ag1 - agent ?ag2 - agent ?ag3 - agent ?ag4 - agent)
        :precondition (and
            (tribe-has-food)
            (has-fork ?ag1)
            (has-fork ?ag2)
            (has-fork ?ag3)
            (has-fork ?ag4)
            (hungry ?ag1)
            (hungry ?ag2)
            (hungry ?ag3)
            (hungry ?ag4)
        )
        :effect (and
            (not (tribe-has-food))
            (not (hungry ?ag1))
            (not (hungry ?ag2))
            (not (hungry ?ag3))
            (not (hungry ?ag4))
        )
    )

    (:action wait
        :parameters (?ag - agent)
        :precondition (and (not (hungry ?ag)))
        :effect (and (hungry ?ag))
    )

)
