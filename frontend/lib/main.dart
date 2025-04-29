import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const SoundtrackApp());
}

class SoundtrackApp extends StatelessWidget {
  const SoundtrackApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Artistify',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange[600]!),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
 