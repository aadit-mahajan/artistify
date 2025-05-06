import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'results_screen.dart';
import 'dart:ui';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LoadingScreen extends StatefulWidget {
  final String story;
  final String? artist; // optional artist parameter

  const LoadingScreen({super.key, required this.story, this.artist}); 

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen> {
  void _showError(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Something went wrong'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context).pop(); // Go back to home screen
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<Map<String, String>?> _fetchImageAndArtist(String song) async {
    try {
      final response = await http.get(
        Uri.parse('https://alert-glider-annually.ngrok-free.app/get_track_data?track_name=$song'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'ngrok-skip-browser-warning': 'skip-browser-warning',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final imageUrl = data['track_data']['image_link'] ?? '';
        final artist = data['track_data']['artist'] ?? 'Unknown Artist';
        return {
          'image_url': imageUrl,
          'artist': artist,
        };
      } else {
        _showError('We couldn\'t fetch song details for "$song". Skipping this song.');
      }
    } catch (e) {
      _showError('Network issue while fetching details for "$song". Please try again later.');
    }
    return null;
  }


  @override
  void initState() {
    super.initState();
    _simulateApiCall();
  }

  Future<void> _simulateApiCall() async {
  try {
    final response = await http.post(
      Uri.parse('https://alert-glider-annually.ngrok-free.app/generate_soundtrack'),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'ngrok-skip-browser-warning': 'skip-browser-warning',
      },
      body: jsonEncode({
        'storyline': widget.story,
        'artist': widget.artist ?? '',
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      var artist = data['Chosen artist'] ?? 'Unknown Artist';
      final List<Map<String, String>> sceneTrackPairs = [];

      for (var entry in data.entries) {
        var key = entry.key;
        var value = entry.value;
        if (key.startsWith('Scene')) {
          final data = await _fetchImageAndArtist(value['assigned_song'] ?? '');
          final imageUrl = data?['image_url'] ?? '';
          artist = data?['artist'] ?? 'Unknown Artist';
          sceneTrackPairs.add({
            'scene': value['scene_text'] ?? '',
            'track': value['assigned_song'] ?? '',
            'image_url': imageUrl,
            'artist': artist,
          });
        }
      }

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(
            story: widget.story,
            sceneTrackPairs: sceneTrackPairs,
          ),
        ),
      );
    } else {
      _showError(
        'Oops! We couldn\'t generate your soundtrack at the moment. Please try again later.',
      );
    }
  } catch (e) {
    _showError(
      'Something went wrong while connecting to the server. Please check your internet connection and try again.',
    );
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text(
          "Artistify - Soundtrack your Story",
          style: GoogleFonts.parisienne(
            fontSize: 25,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(30),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SpinKitFadingCircle(
                  color: Colors.white,
                  size: 60.0,
                ),
                const SizedBox(height: 30),
                Text(
                  'Generating your soundtrack...',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.notoSerif(
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  widget.artist != null && widget.artist!.isNotEmpty
                      ? 'Customizing with artist: ${widget.artist}...'
                      : 'Sit tight, magic is happening!',
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    color: Colors.white70,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
