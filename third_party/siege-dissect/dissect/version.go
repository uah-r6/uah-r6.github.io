package dissect

const (
	Y7S1        int = 6884476
	Y7S2        int = 7040830
	Y7S4        int = 7338571
	Y8S1        int = 7408213
	Y8S2        int = 7601998
	Y8S3        int = 7762708
	Y8S4        int = 7921866
	Y9S1        int = 8111697
	Y9S1Update3 int = 8211379
	Y9S2        int = 8303162
	Y9S3        int = 8506016
	Y9S4        int = 8673114
	Y10S1       int = 8825661
	Y10S1_1     int = 8863180
	Y10S1_2     int = 8882422
	Y10S1_3     int = 8908078
	Y10S2_1     int = 9034019
	Y10S2_1_1   int = 9058361
	Y10S2_2     int = 9077538
	Y10S2_3     int = 9098584
	Y10S2_4     int = 9124272
	Y10S2_5     int = 9158643
	Y10S3       int = 9199003
	Y10S3_1     int = 9211553

	// Y11 constants below are observed from real replay headers rather than
	// lifted from an upstream release list. Add more builds only after
	// checking the structural action marker and final operator evidence in
	// real replays. Earlier Y11 builds are explicitly gated below; the
	// original UAH Y11S3_Alpha04 behavior remains enabled for later builds.
	Y11S1_Alpha03 int = 9625601
	// Official professional replay builds verified against real rounds.
	Y11S1_Alpha03Pro int = 9636829
	Y11S1_Alpha03SLC int = 9658832
	// All 43 rounds in four official Europe MENA Stage 1 June 8–9 maps
	// have the structural action marker and pre-action operator packets.
	Y11S2_Alpha03EML int = 9718747
	// June 18 North America Stage 1 replays use alternate player identity
	// property hashes. All 24 physical rounds in two official match archives
	// have the structural 0->179 action marker and all 120 final attacker IDs
	// in pre-action operator packets.
	Y11S2_Alpha03NAL int = 9734089
	Y11S2_Alpha04Pro int = 9751808
	Y11S2_Alpha04EML int = 9769907
	Y11S2_Alpha04EWC int = 9820472
	Y11S3_Alpha04EML int = 9879602
	// All 25 rounds in three September North America Stage 2 maps have the
	// structural action marker and all 125 final attacker IDs before it.
	Y11S3_Alpha04NAL int = 9883691
	Y11S3_Alpha04    int = 9901603
)

// Restrict action-start operator selection to verified replay layouts.
func supportsActionStartOperators(codeVersion int) bool {
	return codeVersion == Y11S1_Alpha03Pro || codeVersion == Y11S1_Alpha03SLC ||
		codeVersion == Y11S2_Alpha03EML || codeVersion == Y11S2_Alpha03NAL ||
		codeVersion == Y11S2_Alpha04Pro || codeVersion == Y11S2_Alpha04EML ||
		codeVersion == Y11S2_Alpha04EWC || codeVersion == Y11S3_Alpha04EML ||
		codeVersion == Y11S3_Alpha04NAL ||
		codeVersion >= Y11S3_Alpha04
}
