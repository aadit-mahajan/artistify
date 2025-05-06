import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:ui';

class ResultScreen extends StatelessWidget {
  final String story;
  final List<Map<String, String>> sceneTrackPairs;

  const ResultScreen({
    super.key,
    required this.story,
    required this.sceneTrackPairs,
  });

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
        child: SafeArea(
          child: Center(
            child: Container(
              padding: const EdgeInsets.all(24),
              constraints: const BoxConstraints(maxWidth: 900),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '🎬 Scenes & Soundtracks',
                    style: GoogleFonts.notoSerif(
                      fontSize: 32,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                
                  const SizedBox(height: 16),
                  Expanded(
                    child: ListView.separated(
                      itemCount: sceneTrackPairs.length,
                      separatorBuilder: (context, index) => const SizedBox(height: 24),
                      itemBuilder: (context, index) {
                        final scene = sceneTrackPairs[index]['scene'] ?? 'Unknown Scene';
                        final fullTrack = sceneTrackPairs[index]['track'] ?? 'Unknown Track';
                        final imageUrl = sceneTrackPairs[index]['image_url'];
                        final artist = sceneTrackPairs[index]['artist'] ?? 'Unknown Artist';
                        String trackTitle = fullTrack;
                        if (fullTrack.contains(' - ')) {
                          final parts = fullTrack.split(' - ');
                          if (parts.length >= 2) {
                            trackTitle = parts[1];
                          }
                        }

                        return ClipRRect(
                          borderRadius: BorderRadius.circular(20),
                          child: BackdropFilter(
                            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                            child: Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: Colors.white.withAlpha(15),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: Colors.white.withAlpha(50),
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // LEFT: Scene description
                                  Expanded(
                                    flex: 3,
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Scene ${index + 1}',
                                          style: GoogleFonts.notoSerif(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          scene,
                                          style: GoogleFonts.notoSerif(
                                            fontSize: 16,
                                            color: Colors.white,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),

                                  const SizedBox(width: 16),
                                  // RIGHT: Album art + artist + track
                                  Expanded(
                                    flex: 2,
                                    child: Align(
                                      alignment: Alignment.centerRight,
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.end,
                                        children: [
                                          ClipRRect(
                                            borderRadius: BorderRadius.circular(12),
                                            child: imageUrl != null
                                              ? Image.network(
                                                  imageUrl,
                                                  height: 100,
                                                  width: 100,
                                                  fit: BoxFit.cover,
                                                  errorBuilder: (context, error, stackTrace) => Container(
                                                    height: 100,
                                                    width: 100,
                                                    color: Colors.grey.withAlpha(50),
                                                    child: const Icon(Icons.broken_image, color: Colors.white),
                                                  ),
                                                )
                                              : Container(
                                                  height: 100,
                                                  width: 100,
                                                  color: Colors.grey.withAlpha(50),
                                                  child: const Icon(Icons.image_not_supported, color: Colors.white),
                                                ),
                                          ),
                                          const SizedBox(height: 8),
                                          if (artist.isNotEmpty) ...[
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.end,
                                              children: [
                                                const Icon(Icons.person, color: Colors.white, size: 18),
                                                const SizedBox(width: 4),
                                                Flexible(
                                                  child: Text(
                                                    artist,
                                                    style: GoogleFonts.notoSans(
                                                      fontSize: 14,
                                                      fontWeight: FontWeight.bold,
                                                      color: Colors.white,
                                                    ),
                                                    textAlign: TextAlign.right,
                                                    overflow: TextOverflow.visible,
                                                  ),
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 4),
                                          ],
                                          Row(
                                            mainAxisAlignment: MainAxisAlignment.end,
                                            children: [
                                              const Icon(Icons.music_note, color: Colors.white, size: 18),
                                              const SizedBox(width: 4),
                                              Flexible(
                                                child: Text(
                                                  trackTitle,
                                                  style: const TextStyle(
                                                    fontSize: 14,
                                                    fontStyle: FontStyle.italic,
                                                    color: Colors.white,
                                                  ),
                                                  textAlign: TextAlign.right,
                                                  overflow: TextOverflow.visible, 
                                                ),
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.arrow_back, color: Colors.white),
                      label: Text(
                        'Back to Input',
                        style: GoogleFonts.poppins(color: Colors.white),
                      ),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.white),
                      ),
                    ),
                  )
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
