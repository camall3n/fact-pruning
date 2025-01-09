(define (problem minecraft-small-2)

(:domain minecraft-small)

(:objects steve something)

(:init
    ; (has-food steve)
    ; (has-sticks steve)
    ; (has-stone steve)
    (hungry steve)
    ; (has-axe steve)
)

(:goal (and
        (hungry steve)
        (has-food steve)
    )
)

)
