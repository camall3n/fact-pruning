(define (domain minecraft-multi)
    (:requirements :strips)

    (:functions
        (total-cost) - number
    )

    (:predicates
        (tribe-has-food)
        (hungry ?ag)
        (has-logs ?ag)
        (has-planks ?ag)
        (has-sticks ?ag)
        (has-stone ?ag)
        (has-iron ?ag)
        (has-wool ?ag)
        (has-wood-pickaxe ?ag)
        (has-stone-pickaxe ?ag)
        (has-stone-axe ?ag)
        (has-shears ?ag)
        (has-fork ?ag)
        (has-bed ?ag)
    )

    ; ---------- resources ----------

    (:action chop-tree
        :parameters (?ag)
        :precondition ()
        :effect (and (has-logs ?ag))
    )

    (:action destroy-bush
        :parameters (?ag)
        :precondition ()
        :effect (and (has-sticks ?ag))
    )

    (:action mine-stone
        :parameters (?ag)
        :precondition (or
            (has-wood-pickaxe ?ag)
            (has-stone-pickaxe ?ag)
        )
        :effect (and (has-stone ?ag))
    )

    (:action mine-iron
        :parameters (?ag)
        :precondition (and (has-stone-pickaxe ?ag))
        :effect (and (has-iron ?ag))
    )

    (:action shear-sheep
        :parameters (?ag)
        :precondition (and (has-shears ?ag))
        :effect (and (has-wool ?ag))
    )

    ; ---------- crafting ----------

    (:action craft-planks
        :parameters (?ag)
        :precondition (and (has-logs ?ag))
        :effect (and
            (not (has-logs ?ag))
            (has-planks ?ag)
        )
    )

    (:action craft-wood-pickaxe
        :parameters (?ag1 ?ag2 ?ag3)
        :precondition (and
            (has-sticks ?ag1)
            (has-planks ?ag2)
            (not (has-wood-pickaxe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1))
            (not (has-planks ?ag2))
            (has-wood-pickaxe ?ag3)
        )
    )

    (:action craft-stone-pickaxe
        :parameters (?ag1 ?ag2 ?ag3)
        :precondition (and
            (has-sticks ?ag1)
            (has-stone ?ag2)
            (not (has-stone-pickaxe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1))
            (not (has-stone ?ag2))
            (has-stone-pickaxe ?ag3)
        )
    )

    (:action craft-stone-axe
        :parameters (?ag1 ?ag2 ?ag3)
        :precondition (and
            (has-sticks ?ag1)
            (has-stone ?ag2)
            (not (has-stone-axe ?ag3))
        )
        :effect (and
            (not (has-sticks ?ag1))
            (not (has-stone ?ag2))
            (has-stone-axe ?ag3)
        )
    )

    (:action craft-shears
        :parameters (?ag)
        :precondition (and
            (has-iron ?ag)
            (not (has-shears ?ag))
        )
        :effect (and
            (not (has-iron ?ag))
            (has-shears ?ag)
        )
    )

    (:action craft-fork
        :parameters (?ag)
        :precondition (and
            (has-iron ?ag)
            (not (has-fork ?ag))
        )
        :effect (and
            (not (has-iron ?ag))
            (has-fork ?ag)
        )
    )

    (:action craft-bed
        :parameters (?ag)
        :precondition (and
            (has-wool ?ag)
            (has-planks ?ag)
            (not (has-bed ?ag))
        )
        :effect (and
            (not (has-wool ?ag))
            (not (has-planks ?ag))
            (has-bed ?ag)
        )
    )

    ; ---------- food ----------

    (:action hunt
        :parameters (?ag)
        :precondition (and (not (hungry ?ag)))
        :effect (and
            (tribe-has-food)
            (hungry ?ag)
            (increase (total-cost) 50)
        )
    )

    (:action gather
        :parameters (?ag)
        :precondition (and (hungry ?ag))
        :effect (and
            (tribe-has-food)
            (increase (total-cost) 50)
        )
    )

    (:action eat
        :parameters (?ag)
        :precondition (and
            (tribe-has-food)
            (has-fork ?ag)
            (hungry ?ag)
        )
        :effect (and
            (not (tribe-has-food))
            (not (hungry ?ag))
        )
    )

    (:action wait
        :parameters (?ag)
        :precondition (and (not (hungry ?ag)))
        :effect (and (hungry ?ag))
    )

)
