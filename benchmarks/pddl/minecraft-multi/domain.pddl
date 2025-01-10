(define (domain minecraft-multi)
    (:requirements :strips :disjunctive-preconditions)

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
        :parameters (?ag)
        :precondition (and
            (has-sticks ?ag)
            (has-planks ?ag)
            (not (has-wood-pickaxe ?ag))
        )
        :effect (and
            (not (has-sticks ?ag))
            (not (has-planks ?ag))
            (has-wood-pickaxe ?ag)
        )
    )

    (:action craft-stone-pickaxe
        :parameters (?ag)
        :precondition (and
            (has-sticks ?ag)
            (has-stone ?ag)
            (not (has-stone-pickaxe ?ag))
        )
        :effect (and
            (not (has-sticks ?ag))
            (not (has-stone ?ag))
            (has-stone-pickaxe ?ag)
        )
    )

    (:action craft-stone-axe
        :parameters (?ag)
        :precondition (and
            (has-sticks ?ag)
            (has-stone ?ag)
            (not (has-stone-axe ?ag))
        )
        :effect (and
            (not (has-sticks ?ag))
            (not (has-stone ?ag))
            (has-stone-axe ?ag)
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
        )
    )

    (:action gather
        :parameters (?ag)
        :precondition (and (hungry ?ag))
        :effect (and (tribe-has-food))
    )

    (:action eat
        :parameters (?ag)
        :precondition (and
            (tribe-has-food)
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
