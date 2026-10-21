class TrakivoRAG:
    def __init__(self):
        self.entries = [
            (('brake','braking','temp','temperature'), 'Brake temperature must be interpreted using the sensor location, vehicle, and validated series-specific operating limits. Heat can affect braking consistency.', 'Safety/Brakes'),
            (('wing','aero','understeer'), 'Front-wing changes affect aerodynamic balance, but the direction and magnitude depend on car setup, speed, ride height, and conditions.', 'Aerodynamics'),
            (('oil','pressure','lubrication'), 'Compare oil pressure with manufacturer operating ranges and operating conditions; validate the sensor before diagnosing a lubrication fault.', 'Powertrain'),
        ]
    def retrieve_context(self, query: str) -> str:
        q=query.lower()
        for words, content, category in self.entries:
            if any(w in q for w in words): return f'[{category}] {content}'
        return '[General] Separate measured observations from hypotheses and check validated baselines before drawing engineering conclusions.'
